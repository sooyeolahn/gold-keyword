import time
import hmac
import hashlib
import base64
import json
import pandas as pd
import urllib.parse
from datetime import datetime
from collections import deque
import asyncio
import aiohttp
from supabase import create_client, Client

# 사용자 설정 정보 (검색광고 API)
NAVER_SEARCH_ACCESS_LICENSE_KEY = "0100000000975672973f5cbb17b6d499d30d8094007fda425c13391713e83c42bd48d01e4b"
NAVER_SEARCH_SECRET_KEY = "AQAAAACXVnKXP1y7F7bUmdMNgJQAzwCI2CsPUAcb/RrTubSHew=="
NAVER_SEARCH_CUSTOMER_ID = "4265176"

# 검색 API 설정 정보 (문서수 조회용)
NAVER_CLIENT_ID = "e8blHtEDGvL4FXttaDKK"
NAVER_CLIENT_SECRET = "xEMocB4h_i"

# Supabase 설정
SUPABASE_URL = "https://zhncrmrwircbhqrgkmab.supabase.co"
SUPABASE_KEY = "sb_secret_qeEA44WqQDhc8lpVh0o7Dw_jc9uC6f9"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = "https://api.naver.com"

def generate_signature(timestamp, method, uri, secret_key):
    message = f"{timestamp}.{method}.{uri}"
    digest = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")

def get_header(method, uri, api_key, secret_key, customer_id):
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, method, uri, secret_key)
    
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": str(customer_id),
        "X-Signature": signature
    }

async def get_keyword_stats(session, hint_keywords, semaphore):
    uri = "/keywordstool"
    method = "GET"
    
    headers = get_header(method, uri, NAVER_SEARCH_ACCESS_LICENSE_KEY, NAVER_SEARCH_SECRET_KEY, NAVER_SEARCH_CUSTOMER_ID)
    
    params = {
        "hintKeywords": hint_keywords,
        "showDetail": 1
    }
    
    max_retries = 5
    base_delay = 1.0

    async with semaphore:
        for attempt in range(max_retries):
            try:
                async with session.get(BASE_URL + uri, params=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"Ad API Rate Limit(429): {wait_time}초 대기 후 재시도 ({attempt+1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        text = await response.text()
                        # print(f"Ad API Error Code: {response.status}")
                        # print(f"Error Message: {text}")
                        return None
            except Exception as e:
                print(f"Ad API 요청 중 오류 발생: {e}")
                return None
        return None

async def get_blog_document_count(session, keyword, semaphore):
    """
    네이버 블로그 검색 API를 사용하여 해당 키워드의 문서 수를 조회합니다. (비동기)
    재시도 로직 추가 (Rate Limit 대응)
    """
    max_retries = 5
    base_delay = 1.0

    async with semaphore:
        for attempt in range(max_retries):
            try:
                encText = urllib.parse.quote(keyword)
                url = "https://openapi.naver.com/v1/search/blog?query=" + encText
                
                headers = {
                    "X-Naver-Client-Id": NAVER_CLIENT_ID,
                    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        return json_data.get('total', 0)
                    elif response.status == 429:
                        # Rate Limit 걸림 -> 대기 후 재시도
                        text = await response.text()
                        if "Query limit exceeded" in text or "010" in text:
                            print(f"[Fatal] Daily Quota Exceeded: {text}")
                            return -2 # Special code for Quota Exceeded

                        wait_time = base_delay * (2 ** attempt) # Exponential Backoff
                        print(f"Rate Limit(429) 발생: '{keyword}' - {wait_time}초 대기 후 재시도 ({attempt+1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        text = await response.text()
                        print(f"문서수 조회 실패 ({keyword}): {response.status} - {text}")
                        return -1 # 에러 발생 시 -1 반환
            except Exception as e:
                print(f"문서수 조회 중 예외 발생 ({keyword}): {e}")
                return -1 # 에러 발생 시 -1 반환
        
        print(f"'{keyword}' 문서수 조회 실패 (최대 재시도 횟수 초과)")
        return -1 # 최대 재시도 초과 시 -1 반환

def parse_cnt(cnt):
    if isinstance(cnt, str):
        if "<" in cnt:
            return 0
        return int(cnt.replace(',', ''))
    return cnt if cnt else 0

async def process_keyword_item(session, item, collected_keywords, final_results, target_count, queue, queried_keywords, blog_semaphore, result_lock):
    """
    개별 키워드 아이템 처리 (문서수 조회 및 결과 저장)
    """
    # 락 없이 1차 체크 (불필요한 연산 방지)
    if len(final_results) >= target_count:
        return

    rel_keyword = item.get('relKeyword')
    pc_cnt = item.get('monthlyPcQcCnt')
    mobile_cnt = item.get('monthlyMobileQcCnt')
    
    # 중복 체크
    if rel_keyword in collected_keywords:
        return

    # 결과 데이터 파싱
    pc_val = parse_cnt(pc_cnt)
    mobile_val = parse_cnt(mobile_cnt)
    total_val = pc_val + mobile_val
    
    # 문서수 조회 (비동기) - Rate Limit 재시도 로직 포함됨
    doc_count = await get_blog_document_count(session, rel_keyword, blog_semaphore)
    
    # 데이터 유효성 검사 (0건 또는 에러 방지)
    # 0. 쿼리 한도 초과 시 즉시 중단
    if doc_count == -2:
        raise Exception("Daily Quota Exceeded")

    # 1. 검색량이 0인 경우 (API에서 "< 10" 등으로 반환된 경우 포함) 수집 제외
    if total_val == 0:
        return

    # 2. 문서수 조회에 실패한 경우 (-1 반환) 수집 제외
    if doc_count == -1:
        return
    
    # 경쟁율 계산
    if total_val > 0:
        comp_rate = doc_count / total_val
    else:
        comp_rate = 0
    
    # 결과 저장 (Lock 사용으로 정확한 개수 제어 및 중복 방지)
    async with result_lock:
        if len(final_results) >= target_count:
            return

        if rel_keyword not in collected_keywords:
            collected_keywords.add(rel_keyword)
            
            final_results.append({
                "키워드": rel_keyword,
                "월간PC검색수": pc_val,
                "월간모바일검색수": mobile_val,
                "총월간검색수": total_val,
                "문서수": doc_count,
                "경쟁율": comp_rate
            })
            
            # 진행 상황 출력 (100개 단위)
            if len(final_results) % 100 == 0:
                print(f"현재 수집됨: {len(final_results)}/{target_count}")

            # 큐에 추가 (BFS) - 이미 조회했거나 큐에 있는지는 여기서 굳이 락 걸 필요 없음 (queried_keywords는 main loop에서 체크)
            if rel_keyword not in queried_keywords:
                queue.append(rel_keyword)

async def main(initial_keyword=None, target_count=None):
    # 1. 초기 키워드 입력 (인자가 없으면 사용자 입력)
    if initial_keyword is None:
        initial_keyword = input("검색할 키워드를 입력하세요 (예: 원피스): ").strip()
    
    if not initial_keyword:
        print("키워드가 입력되지 않았습니다.")
        return

    # 2. 수집할 키워드 개수 입력 (인자가 없으면 사용자 입력)
    if target_count is None:
        try:
            target_count = int(input("수집할 키워드 개수를 입력하세요 (예: 100): ").strip())
        except ValueError:
            print("숫자를 입력해야 합니다.")
            return

    print(f"'{initial_keyword}' 관련 키워드 수집 시작 (목표: {target_count}개)...")
    print("비동기 처리 방식으로 고속 수집을 시작합니다. (안정성 강화 모드)")

    # API 동시 호출 제한 (Rate Limiting)
    # 블로그 검색 API 제한을 20 -> 5로 하향 조정하여 429 에러 방지
    search_ad_semaphore = asyncio.Semaphore(5)    
    blog_search_semaphore = asyncio.Semaphore(5) 
    
    # 결과 리스트 동기화를 위한 락
    result_lock = asyncio.Lock()

    queue = deque([initial_keyword])
    queried_keywords = set()
    collected_keywords = set()
    final_results = []
    
    async with aiohttp.ClientSession() as session:
        while len(final_results) < target_count and queue:
            # 큐에서 키워드 하나 가져오기
            current_keyword = queue.popleft()
            
            if current_keyword in queried_keywords:
                continue
                
            queried_keywords.add(current_keyword)
            
            # 검색광고 API 호출 (연관 키워드 가져오기)
            # print(f"API 조회 중: {current_keyword}...") 
            result = await get_keyword_stats(session, current_keyword, search_ad_semaphore)
            
            if result and 'keywordList' in result:
                data_list = result['keywordList']
                
                # 가져온 연관 키워드 리스트에 대해 병렬로 문서수 조회 및 처리
                tasks = []
                for item in data_list:
                    # 루프 시작 전 1차 체크
                    if len(final_results) >= target_count:
                        break
                    
                    # 이미 수집된 키워드는 패스
                    if item.get('relKeyword') in collected_keywords:
                        continue
                        
                    task = asyncio.create_task(
                        process_keyword_item(
                            session, 
                            item, 
                            collected_keywords, 
                            final_results, 
                            target_count, 
                            queue, 
                            queried_keywords,
                            blog_search_semaphore,
                            result_lock
                        )
                    )
                    tasks.append(task)
                
                # 현재 배치의 모든 Task가 완료될 때까지 대기
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 예외 체크 (Quota Exceeded 등)
                    stop_collection = False
                    for res in results:
                        if isinstance(res, Exception):
                            if "Daily Quota Exceeded" in str(res):
                                print("\n[Stop] 일일 쿼리 한도 초과로 수집을 조기 종료합니다.")
                                stop_collection = True
                                break
                            # 다른 예외는 무시하거나 로그
                            # print(f"Task Exception: {res}")
                    
                    if stop_collection:
                        queue.clear() # 큐를 비워 루프 종료
                        break
                    
            else:
                pass
            
            # 목표 달성 체크
            if len(final_results) >= target_count:
                break

    # 4. Supabase DB로 저장
    if final_results:
        print(f"\nSupabase DB 저장 중... (총 {len(final_results)}건)")
        
        try:
            # 대량 데이터 삽입 (Batch Insert)
            # Supabase는 한 번에 너무 많은 데이터를 넣으면 에러가 날 수 있으므로 1000개씩 끊어서 넣음
            batch_size = 1000
            for i in range(0, len(final_results), batch_size):
                batch = final_results[i:i + batch_size]
                
                # DB 컬럼명에 맞게 데이터 변환
                db_data = []
                for item in batch:
                    db_data.append({
                        "keyword": item["키워드"],
                        "pc_search_volume": item["월간PC검색수"],
                        "mobile_search_volume": item["월간모바일검색수"],
                        "total_search_volume": item["총월간검색수"],
                        "document_count": item["문서수"],
                        "competition_rate": item["경쟁율"]
                        # created_at은 DB에서 자동 생성
                    })
                
                # Upsert 실행 (keyword 기준 중복 시 업데이트)
                response = supabase.table("keywords").upsert(db_data, on_conflict="keyword").execute()
                print(f" - {i + len(batch)}/{len(final_results)} 저장 완료")
                
            print(f"모든 데이터가 Supabase 'keywords' 테이블에 저장되었습니다.")
            
        except Exception as e:
            print(f"\nSupabase 저장 중 오류 발생: {e}")
            # 백업: 엑셀로 저장
            filename = f"{initial_keyword}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            print(f"백업 파일을 생성합니다: {filename}")
            df = pd.DataFrame(final_results)
            df = df[["키워드", "월간PC검색수", "월간모바일검색수", "총월간검색수", "문서수", "경쟁율"]]
            df.to_excel(filename, index=False)
            
    else:
        print("\n수집된 결과가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
