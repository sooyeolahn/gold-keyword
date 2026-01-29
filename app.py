import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import time

# --- Configuration ---
# Streamlit Cloud 배포 시 secrets에서 로드, 로컬/실패 시 하드코딩 값 사용
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
except Exception:
    SUPABASE_URL = "https://zhncrmrwircbhqrgkmab.supabase.co"
    SUPABASE_KEY = "sb_secret_qeEA44WqQDhc8lpVh0o7Dw_jc9uC6f9"

# --- Page Setup ---
st.set_page_config(
    page_title="꿀키워드",
    page_icon="🍯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Styling ---
st.markdown("""
<style>
    /* Global Styles */
    [data-testid="stAppViewContainer"] {
        background-color: #f0f2f5; /* Light Gray Background */
    }
    .main {
        background-color: #f0f2f5;
    }
    
    /* Search Bar Styling (Pill Shape) */
    .stTextInput > div > div > input {
        border-radius: 50px; /* Fully rounded */
        padding: 12px 25px;
        border: 2px solid #222; /* Darker border as requested */
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        color: #333;
        background-color: white;
        font-size: 1.0em;
    }
    
    /* Category Filters */
    .filter-container {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
        flex-wrap: wrap;
        justify-content: center;
    }
    .filter-btn {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 20px;
        padding: 6px 18px;
        font-size: 0.9em;
        color: #555;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .filter-btn.active {
        background-color: #ff4b4b;
        color: white;
        border-color: #ff4b4b;
    }
    
    /* Card Styling */
    .card {
        background-color: white;
        border-radius: 16px;
        padding: 15px 25px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        border: 1px solid white;
        transition: transform 0.2s;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
    }
    
    .keyword-section {
        display: flex;
        flex-direction: column;
        gap: 4px;
        flex: 1.2;
    }
    
    .meta-info {
        display: flex;
        gap: 8px;
        font-size: 0.75em;
        color: #888;
        align-items: center;
    }
    
    .badge {
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85em;
    }
    
    .keyword-title {
        font-size: 1.1em;
        font-weight: 700;
        color: #1a1a1a;
    }
    
    .metrics-section {
        display: flex;
        gap: 20px;
        align-items: center;
        flex: 2;
        justify-content: flex-end;
    }
    
    .metric {
        text-align: center;
        min-width: 70px;
    }
    
    .metric-label {
        font-size: 0.7em;
        color: #888;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 1.0em;
        font-weight: 700;
        color: #333;
    }
    
    /* Header Styling */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        padding: 10px 10px;
    }
    
    .app-title {
        font-size: 2.0em;
        font-weight: 900;
        color: #222;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: -0.5px;
    }
    
    .logo-icon {
        background-color: #ffca28; /* Honey Color */
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4em;
        box-shadow: 0 4px 6px rgba(255, 202, 40, 0.3);
    }
    
    /* Custom Multiselect Styling */
    .stMultiSelect > div > div {
        background-color: white;
        border-radius: 12px;
        border: 1px solid #ddd;
    }

    /* Copy Button & Code Block Styling */
    [data-testid="stCode"] {
        border: none;
        padding: 0;
        background-color: transparent;
    }
    [data-testid="stCode"] > div {
        background-color: #f8f9fa !important; /* Light background for code block */
        border-radius: 8px;
    }
    [data-testid="stCode"] pre {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #1a1a1a !important;
    }
    [data-testid="stCopyButton"] {
        color: #888;
    }
    [data-testid="stCopyButton"]:hover {
        color: #f57f17;
    }
    
    /* Card Styling using Native Container */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        border: 1px solid white;
        padding: 15px;
        transition: transform 0.2s;
        margin-bottom: 10px;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        border-color: #f0f2f5;
    }
    
    /* Remove default border of st.container(border=True) if possible, or override it above */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        /* Inner content adjustment */
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_data(supabase, page=1, page_size=50, search_query="", sort_options=None):
    try:
        # 쿼리 시작 (전체 카운트 포함)
        query = supabase.table("keywords").select("*", count="exact")
        
        # 검색어 필터
        if search_query:
            query = query.ilike("keyword", f"%{search_query}%")
            
        # 정렬 적용 (DB 레벨)
        # sort_options 예: [('competition_rate', True), ('total_search_volume', False)] 
        # (True: 오름차순/낮은순, False: 내림차순/높은순)
        if sort_options:
            for col, ascending in sort_options:
                query = query.order(col, desc=not ascending)
        else:
            # 기본 정렬: 최신순
            query = query.order("created_at", desc=True)
            
        # 페이징 적용 (0-based index)
        start = (page - 1) * page_size
        end = start + page_size - 1
        query = query.range(start, end)
        
        response = query.execute()
        return pd.DataFrame(response.data), response.count
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(), 0

# --- Main App Logic ---
def main():
    supabase = init_supabase()
    
    # Session State for Pagination
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
        
    def reset_page():
        st.session_state.current_page = 1
    
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="app-title">
            <div class="logo-icon">🍯</div>
            꿀키워드
        </div>
        <div>
            <span style="color: #666; font-size: 0.9em; font-weight: 500;">스마트한 키워드 발굴 도구</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Search & Sort Area
    # Using columns to arrange search and sort
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "", 
            placeholder="분석하고 싶은 주제를 입력하세요 (예: 제주도, 아이폰16)", 
            label_visibility="collapsed",
            on_change=reset_page
        )
        
    with col2:
        # Multi-select for flexible sorting
        sort_options_ui = [
            "경쟁률 (낮은순)", 
            "경쟁률 (높은순)", 
            "조회수 (높은순)", 
            "조회수 (낮은순)",
            "발행수 (높은순)", 
            "발행수 (낮은순)"
        ]
        selected_sorts = st.multiselect(
            "정렬 기준 (선택한 순서대로 적용됩니다)",
            options=sort_options_ui,
            default=["경쟁률 (낮은순)", "조회수 (높은순)"],
            label_visibility="collapsed",
            placeholder="정렬 기준 선택 (여러 개 가능)",
            on_change=reset_page
        )

    # Category Filters (Visual Only)
    categories = ["전체", "영화", "게임", "드라마", "공연·전시", "스타·연예인", "방송", "일상·생각", "문화·책", "육아·결혼", "반려동물"]
    st.markdown(f"""
    <div class="filter-container">
        {''.join([f'<div class="filter-btn {"active" if c == "전체" else ""}">{c}</div>' for c in categories])}
    </div>
    """, unsafe_allow_html=True)
    
    # Data Processing
    page_size = 50
    
    # 정렬 옵션 파싱
    db_sort_options = []
    if selected_sorts:
        for sort_opt in selected_sorts:
            if "경쟁률" in sort_opt:
                db_sort_options.append(("competition_rate", "낮은순" in sort_opt))
            elif "조회수" in sort_opt:
                db_sort_options.append(("total_search_volume", "낮은순" in sort_opt))
            elif "발행수" in sort_opt:
                db_sort_options.append(("document_count", "낮은순" in sort_opt))
    
    with st.spinner("데이터 분석 중..."):
        df, total_count = fetch_data(
            supabase, 
            page=st.session_state.current_page, 
            page_size=page_size, 
            search_query=search_query,
            sort_options=db_sort_options
        )
    
    # Results Header & Pagination Info
    if not df.empty:
        total_pages = (total_count + page_size - 1) // page_size
        
        st.markdown(f"""
        <div style="text-align: center; color: #888; font-size: 0.8em; margin-bottom: 20px; letter-spacing: 1px;">
            SMART SORT APPLIED (DB)
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; color: #666; font-size: 0.9em;">
            <div>Page <strong>{st.session_state.current_page}</strong> / {total_pages}</div>
            <div>TOTAL <strong style="margin-left: 5px; color: #ffca28;">{total_count} Keywords</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
        # List Items
        for _, row in df.iterrows():
            # Format numbers
            total_search_val = row.get('total_search_volume', 0)
            pc_search_val = row.get('pc_search_volume', 0)
            mobile_search_val = row.get('mobile_search_volume', 0)
            
            # Handle None
            total_search_val = total_search_val if total_search_val is not None else 0
            pc_search_val = pc_search_val if pc_search_val is not None else 0
            mobile_search_val = mobile_search_val if mobile_search_val is not None else 0
            
            total_search = f"{total_search_val:,}"
            pc_search = f"{pc_search_val:,}"
            mobile_search = f"{mobile_search_val:,}"
            
            doc_count_val = row.get('document_count', 0)
            doc_count_val = doc_count_val if doc_count_val is not None else 0
            doc_count = f"{doc_count_val:,}"
            
            comp_rate = row.get('competition_rate', 0)
            comp_rate_str = f"{comp_rate:.2f}" if comp_rate is not None else "-"
            
            # Date formatting
            created_at = row.get('created_at', '')
            if created_at:
                try:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%Y.%m.%d %H:%M')
                except:
                    date_str = created_at
            else:
                date_str = "-"
                
            # Determine badge
            badge_text = "일반"
            badge_color = "#e3f2fd" # Blue
            badge_text_color = "#1976d2"
            
            if comp_rate is not None and comp_rate < 0.5:
                badge_text = "🍯 꿀키워드"
                badge_color = "#fff8e1" # Honey Light
                badge_text_color = "#f57f17"
            elif total_search_val > 100000:
                badge_text = "🔥 인기"
                badge_color = "#ffebee" # Red
                badge_text_color = "#c62828"
                
            # Render Card (Native Streamlit with st.code for copy button)
            with st.container(border=True):
                c_left, c_right = st.columns([1.5, 2.5])
                
                with c_left:
                    # Meta info (Badge & Date)
                    st.markdown(f"""
                    <div style="display:flex; gap:8px; align-items:center; margin-bottom:0px;">
                        <span style="background-color: {badge_color}; color: {badge_text_color}; padding: 2px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85em;">{badge_text}</span>
                        <span style="font-size:0.75em; color:#888;">{date_str}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Keyword with Copy Button (Using styled st.code)
                    st.code(row['keyword'], language="text")
                
                with c_right:
                    # Metrics (HTML for layout control)
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; height:100%; padding-top:10px;">
                        <div style="text-align:center; min-width:60px;">
                            <div style="font-size:0.7em; color:#888; margin-bottom:4px;">PC</div>
                            <div style="font-size:0.9em; font-weight:500; color:#666;">{pc_search}</div>
                        </div>
                        <div style="text-align:center; min-width:60px;">
                            <div style="font-size:0.7em; color:#888; margin-bottom:4px;">모바일</div>
                            <div style="font-size:0.9em; font-weight:500; color:#666;">{mobile_search}</div>
                        </div>
                        <div style="text-align:center; min-width:60px;">
                            <div style="font-size:0.7em; color:#888; margin-bottom:4px;">월간 조회</div>
                            <div style="font-size:1.0em; font-weight:700; color:#333;">{total_search}</div>
                        </div>
                        <div style="text-align:center; min-width:60px;">
                            <div style="font-size:0.7em; color:#888; margin-bottom:4px;">월간 발행</div>
                            <div style="font-size:1.0em; font-weight:700; color:#333;">{doc_count}</div>
                        </div>
                        <div style="text-align:center; min-width:60px;">
                            <div style="font-size:0.7em; color:#888; margin-bottom:4px;">경쟁률</div>
                            <div style="font-size:1.0em; font-weight:700; color:#f57f17;">{comp_rate_str}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
        # Pagination Buttons
        col_prev, col_page, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.session_state.current_page > 1:
                if st.button("⬅️ 이전 페이지", use_container_width=True):
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col_next:
            if st.session_state.current_page < total_pages:
                if st.button("다음 페이지 ➡️", use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()
            
    else:
        st.info("데이터가 없습니다. 수집을 시작하거나 검색어를 변경해보세요.")

if __name__ == "__main__":
    main()
