import asyncio
import schedule
import time
from datetime import datetime, date
import random
from 월간총검색수 import main as collect_keywords
from supabase import create_client, Client

# Supabase 설정 (일일 수집량 체크용)
SUPABASE_URL = "https://zhncrmrwircbhqrgkmab.supabase.co"
SUPABASE_KEY = "sb_secret_qeEA44WqQDhc8lpVh0o7Dw_jc9uC6f9"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 하루 최대 수집 목표
DAILY_LIMIT = 24000

# 하루 48번 (30분 간격) 실행을 위한 다양한 분야의 시작 키워드 48개
DAILY_KEYWORDS = [
    # 여행/레저 (5)
    "제주도여행", "캠핑용품", "호캉스", "일본여행", "글램핑",
    # 가전/디지털 (5)
    "공기청정기", "아이패드", "블루투스이어폰", "로봇청소기", "게이밍노트북",
    # 패션/뷰티 (5)
    "여성가방", "남자운동화", "수분크림", "선크림", "명품지갑",
    # 생활/건강 (5)
    "영양제", "마스크", "차량용방향제", "탈모샴푸", "요가매트",
    # 식품/요리 (5)
    "밀키트", "닭가슴살", "커피머신", "와인추천", "다이어트도시락",
    # 육아/키즈 (5)
    "아기물티슈", "어린이장난감", "유모차", "키즈카페", "출산선물",
    # 반려동물 (4)
    "강아지사료", "고양이간식", "애견카페", "강아지옷",
    # 스포츠/취미 (4)
    "골프채", "등산화", "자전거", "낚시용품",
    # 인테리어 (4)
    "조명", "침대매트리스", "사무용의자", "디퓨저",
    # 금융/비즈니스 (3)
    "주식", "재테크", "창업아이템",
    # 교육/도서 (3)
    "영어회화", "자기계발서", "자격증"
]

# 이미 사용한 키워드를 추적하기 위한 인덱스
current_keyword_index = 0

def get_next_keyword():
    global current_keyword_index
    # 키워드 리스트 순회 (하루가 지나면 다시 처음부터? 혹은 매일 랜덤? -> 요구사항: 날짜별로 수집)
    # 여기서는 리스트를 순환하며 하나씩 가져오도록 구현
    keyword = DAILY_KEYWORDS[current_keyword_index % len(DAILY_KEYWORDS)]
    current_keyword_index += 1
    return keyword

def get_today_collected_count():
    """오늘 수집된 키워드 개수를 조회합니다."""
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        
        # 'created_at'이 오늘 날짜인 데이터의 개수 조회 (count='exact', head=True -> 데이터 안 가져오고 개수만)
        response = supabase.table("keywords") \
            .select("id", count="exact", head=True) \
            .gte("created_at", today_start) \
            .lte("created_at", today_end) \
            .execute()
            
        return response.count
    except Exception as e:
        print(f"[오류] 일일 수집량 조회 실패: {e}")
        return 0

def run_collection_job():
    # 1. 일일 한도 체크
    current_count = get_today_collected_count()
    if current_count >= DAILY_LIMIT:
        print(f"\n[스케줄러 건너뜀] {datetime.now()} - 오늘 목표 달성 ({current_count}/{DAILY_LIMIT}개). 수집을 중단합니다.")
        return

    keyword = get_next_keyword()
    target_count = 2000 # 회당 수집 개수
    
    # 남은 개수만큼만 수집하도록 조정 (선택 사항)
    # remaining = DAILY_LIMIT - current_count
    # if target_count > remaining:
    #     target_count = remaining
    
    print(f"\n[스케줄러 실행] {datetime.now()} - 키워드: '{keyword}' 수집 시작 (목표: {target_count}개, 현재 누적: {current_count}개)")
    
    try:
        # 비동기 함수인 main을 동기 스케줄러에서 실행
        asyncio.run(collect_keywords(initial_keyword=keyword, target_count=target_count))
        
        # 완료 후 누적 개수 출력
        final_count = get_today_collected_count()
        print(f"[스케줄러 완료] {datetime.now()} - '{keyword}' 수집 완료 (오늘 누적: {final_count}/{DAILY_LIMIT}개)")
        
    except Exception as e:
        print(f"[스케줄러 오류] {datetime.now()} - 실행 중 오류 발생: {e}")

def start_scheduler():
    print("=== 키워드 자동 수집 스케줄러 시작 (Supabase DB 연동) ===")
    print(f"총 {len(DAILY_KEYWORDS)}개의 시작 키워드로 30분 간격 수집을 진행합니다.")
    print(f"하루 최대 수집 목표: {DAILY_LIMIT}개 (달성 시 당일 수집 중단)")
    
    # 30분마다 실행
    schedule.every(30).minutes.do(run_collection_job)
    
    # 시작하자마자 한번 실행
    run_collection_job()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # 스케줄러 실행 전 필요한 라이브러리 체크 등은 생략 (이미 설치됨)
    start_scheduler()
