import asyncio
from datetime import datetime, timedelta
import sys
import os

# 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scheduler import DAILY_KEYWORDS, get_today_collected_count, DAILY_LIMIT
from 월간총검색수 import main as collect_keywords

def get_keyword_by_time():
    # KST (한국 시간) 기준 현재 시각
    kst_now = datetime.utcnow() + timedelta(hours=9)
    
    # 00:00부터 현재까지의 총 분(minute) 계산
    total_minutes = kst_now.hour * 60 + kst_now.minute
    
    # 30분 단위 구간 인덱스 계산 (0 ~ 47)
    interval_index = int(total_minutes / 30) % 48
    
    # 해당 구간의 키워드 선택
    keyword = DAILY_KEYWORDS[interval_index % len(DAILY_KEYWORDS)]
    return keyword

def run_batch_job():
    print(f"[{datetime.utcnow() + timedelta(hours=9)}] GitHub Actions 배치 작업 시작")
    
    # 1. 일일 한도 체크
    current_count = get_today_collected_count()
    if current_count >= DAILY_LIMIT:
        print(f"[스킵] 오늘 목표 달성 ({current_count}/{DAILY_LIMIT}개). 수집을 건너뜁니다.")
        return

    # 2. 시간 기반 키워드 선정
    keyword = get_keyword_by_time()
    target_count = 2000 # 회당 수집 개수
    
    print(f"[실행] 키워드: '{keyword}' 수집 시작 (목표: {target_count}개, 현재 누적: {current_count}개)")
    
    try:
        # 비동기 수집 실행
        asyncio.run(collect_keywords(initial_keyword=keyword, target_count=target_count))
        
        final_count = get_today_collected_count()
        print(f"[완료] '{keyword}' 수집 완료 (오늘 누적: {final_count}/{DAILY_LIMIT}개)")
        
    except Exception as e:
        print(f"[오류] 실행 중 오류 발생: {e}")
        # GitHub Actions가 실패로 인식하도록 exit code 1 반환 (선택사항, 여기서는 그냥 로그만 남김)
        sys.exit(1)

if __name__ == "__main__":
    run_batch_job()
