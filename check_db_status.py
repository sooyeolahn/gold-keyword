from supabase import create_client, Client
from datetime import datetime

# Supabase 설정
SUPABASE_URL = "https://zhncrmrwircbhqrgkmab.supabase.co"
SUPABASE_KEY = "sb_secret_qeEA44WqQDhc8lpVh0o7Dw_jc9uC6f9"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 오늘 날짜 기준 데이터 조회
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    # 전체 카운트
    response = supabase.table("keywords") \
        .select("id", count="exact", head=True) \
        .execute()
    total_count = response.count
    
    # 오늘 카운트
    today_response = supabase.table("keywords") \
        .select("id", count="exact", head=True) \
        .gte("created_at", today_start) \
        .execute()
    today_count = today_response.count
    
    print(f"\n[Supabase 데이터 현황]")
    print(f"- 현재 총 누적 데이터: {total_count:,}개")
    print(f"- 오늘 수집된 데이터: {today_count:,}개")
    
except Exception as e:
    print(f"조회 실패: {e}")
