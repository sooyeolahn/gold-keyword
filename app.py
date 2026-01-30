import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from supabase import create_client, Client
import datetime
from datetime import timedelta, datetime
import math
import textwrap
import json

# -----------------------------------------------------------------------------
# 1. Configuration & Setup
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
        border-radius: 50px;
        padding: 12px 25px;
        border: 2px solid #222;
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
    
    /* Card Styling (HTML) */
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
    
    /* Copy Button Styles */
    .keyword-wrapper {
        display: inline-flex !important;
        align-items: center !important;
        cursor: pointer;
        user-select: none; /* Prevent text selection on double click */
        transition: opacity 0.1s;
    }
    .keyword-wrapper:active {
        opacity: 0.7;
    }
    
    .keyword-wrapper:hover .copy-icon {
        opacity: 1 !important;
    }
    
    /* On mobile/touch devices where hover isn't primary, show icon */
    @media (hover: none) {
        .copy-icon {
            opacity: 1 !important;
            color: #ccc;
        }
    }
    
    .copy-icon {
        font-size: 1rem;
        color: #bbb;
        margin-left: 8px;
        opacity: 0;
        transition: opacity 0.2s ease-in-out;
    }

</style>

<!-- Global Script for Copy Functionality -->
<script>
(function() {
    console.log("Copy Script Loaded");
    
    // Unique function name to avoid conflicts
    var fnName = "goldKeywordCopy";
    
    var copyFn = function(text, iconId) {
        console.log("Copy Triggered:", text);
        var icon = document.getElementById(iconId);
        
        function showSuccess() {
            if (icon) {
                var originalContent = icon.innerHTML;
                icon.innerHTML = '✅';
                icon.style.opacity = '1';
                setTimeout(function() { 
                    icon.innerHTML = originalContent; 
                    icon.style.opacity = ''; 
                }, 2000);
            }
        }

        function showFail(err) {
            console.error("Copy failed:", err);
            alert("복사 실패: " + err + "\n\n브라우저 보안 설정이나 환경 문제일 수 있습니다.");
        }

        // 1. Try modern Clipboard API
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(showSuccess).catch(function(err) {
                console.warn('Clipboard API failed, trying fallback', err);
                fallbackCopy(text);
            });
        } else {
            fallbackCopy(text);
        }

        // 2. Fallback for older browsers / insecure context
        function fallbackCopy(text) {
            try {
                var textArea = document.createElement("textarea");
                textArea.value = text;
                
                // Make it invisible but part of DOM
                textArea.style.position = "fixed";
                textArea.style.left = "0";
                textArea.style.top = "0";
                textArea.style.opacity = "0";
                
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                var successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (successful) {
                    showSuccess();
                } else {
                    showFail("execCommand returned false");
                }
            } catch (err) {
                showFail(err);
            }
        }
    };
    
    // Attach to window
    window[fnName] = copyFn;
    
    // Attach to parent window just in case (for Streamlit Cloud/iframe)
    try {
        if (window.parent) {
            window.parent[fnName] = copyFn;
        }
    } catch(e) { console.log("Parent access denied"); }
})();
</script>
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
    st.markdown(textwrap.dedent("""
    <div class="header-container">
        <div class="app-title">
            <div class="logo-icon">🍯</div>
            꿀키워드
        </div>
        <div>
            <span style="color: #666; font-size: 0.9em; font-weight: 500;">스마트한 키워드 발굴 도구</span>
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # Search & Sort Area
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
        
        st.markdown(textwrap.dedent(f"""
        <div style="text-align: center; color: #888; font-size: 0.8em; margin-bottom: 20px; letter-spacing: 1px;">
            SMART SORT APPLIED (DB)
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; color: #666; font-size: 0.9em;">
            <div>Page <strong>{st.session_state.current_page}</strong> / {total_pages}</div>
            <div>TOTAL <strong style="margin-left: 5px; color: #ffca28;">{total_count} Keywords</strong></div>
        </div>
        """), unsafe_allow_html=True)
        
        # -----------------------------------------------------------
        # NEW: Unified Component Rendering (Replacing Loop)
        # -----------------------------------------------------------
        
        # Helper: Format numbers
        def fmt(val):
            return f"{val:,}" if val is not None else "0"
            
        def fmt_comp(val):
            return f"{val:.2f}" if val is not None else "-"

        # Prepare Data for Component
        component_data = []
        for i, (_, row) in enumerate(df.iterrows()):
            # Metric Logic
            pc_search_val = row.get('pc_search_volume', 0)
            if pc_search_val is None: pc_search_val = 0
            
            mobile_search_val = row.get('mobile_search_volume', 0)
            if mobile_search_val is None: mobile_search_val = 0
            
            total_search_val = row.get('total_search_volume', 0)
            if total_search_val is None: total_search_val = pc_search_val + mobile_search_val
            
            doc_count_val = row.get('document_count', 0)
            if doc_count_val is None: doc_count_val = 0
            
            comp_rate_val = row.get('competition_rate', 0)
            
            # Badge Logic
            badge_text = "일반"
            badge_color = "#e3f2fd"
            badge_text_color = "#1976d2"
            
            if comp_rate_val is not None and comp_rate_val < 0.5:
                badge_text = "🍯 꿀키워드"
                badge_color = "#fff8e1"
                badge_text_color = "#f57f17"
            elif total_search_val > 100000:
                badge_text = "🔥 인기"
                badge_color = "#ffebee"
                badge_text_color = "#c62828"

            # Date Logic
            created_at = row.get('created_at', '')
            date_str = "-"
            if created_at:
                try:
                    date_obj = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%Y.%m.%d')
                except:
                    date_str = str(created_at)[:10]

            component_data.append({
                "keyword": row['keyword'],
                "badge": {"text": badge_text, "bg": badge_color, "color": badge_text_color},
                "date": date_str,
                "metrics": {
                    "pc": fmt(pc_search_val),
                    "mobile": fmt(mobile_search_val),
                    "total": fmt(total_search_val),
                    "docs": fmt(doc_count_val),
                    "comp": fmt_comp(comp_rate_val)
                }
            })
            
        # Serialize Data
        import json
        data_json = json.dumps(component_data, ensure_ascii=False)
        
        # Component HTML Template
        component_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
                body {{
                    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
                    margin: 0;
                    padding: 4px;
                    background-color: transparent;
                }}
                .card {{
                    background: white;
                    border-radius: 12px;
                    padding: 20px 24px;
                    margin-bottom: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    border: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                /* Left Section: Badge, Date, Keyword */
                .left-section {{
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    min-width: 0; /* Prevent flex overflow */
                }}
                
                .meta-row {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                
                .badge {{
                    padding: 3px 6px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    line-height: 1;
                }}
                
                .date {{
                    font-size: 12px;
                    color: #999;
                }}
                
                .keyword-row {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    cursor: pointer;
                    user-select: none;
                }}
                .keyword-row:active {{ opacity: 0.7; }}
                
                .keyword {{
                    font-size: 18px;
                    font-weight: 700;
                    color: #222;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                
                .copy-btn {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 32px;
                    height: 32px;
                    border-radius: 8px;
                    background-color: transparent;
                    color: #9aa0a6; /* Neutral Gray Icon */
                    border: none;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    margin-left: 6px;
                    padding: 0;
                }}
                
                .keyword-row:hover .copy-btn {{
                    background-color: #f1f3f4; /* Hover: Light Gray BG */
                    color: #5f6368; /* Hover: Darker Gray Icon */
                    opacity: 1;
                }}
                
                .copy-btn.success {{
                    background-color: #e6f4ea !important; /* Success: Light Green BG */
                    color: #1e8e3e !important; /* Success: Green Icon */
                    opacity: 1 !important;
                }}
                
                .copy-btn svg {{
                    width: 18px;
                    height: 18px;
                    fill: none;
                    stroke: currentColor;
                    stroke-width: 2;
                    stroke-linecap: round;
                    stroke-linejoin: round;
                }}
                
                /* Right Section: Metrics */
                .metrics-grid {{
                    display: flex;
                    gap: 32px;
                    align-items: center;
                }}
                
                .metric {{
                    display: flex;
                    flex-direction: column;
                    align-items: center; /* Center align labels and values */
                    min-width: 60px;
                }}
                
                .metric-label {{
                    font-size: 11px;
                    color: #888;
                    margin-bottom: 6px;
                }}
                
                .metric-value {{
                    font-size: 15px;
                    font-weight: 600;
                    color: #333;
                }}
                
                .metric-value.comp {{ color: #f57f17; }}
                
                /* Mobile Layout */
                @media (max-width: 768px) {{
                    .card {{
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 16px;
                        padding: 16px;
                    }}
                    .metrics-grid {{
                        width: 100%;
                        justify-content: space-between;
                        gap: 8px;
                    }}
                    .metric {{
                        min-width: auto;
                    }}
                    .metric-label {{
                        font-size: 10px;
                    }}
                    .metric-value {{
                        font-size: 13px;
                    }}
                    .copy-btn {{ opacity: 1; }}
                }}
            </style>
        </head>
        <body>
            <div id="container"></div>

            <script>
                const data = {data_json};
                const container = document.getElementById('container');
                
                // Icons
                const COPY_ICON = `<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
                const CHECK_ICON = `<svg viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;

                data.forEach((item, index) => {{
                    const card = document.createElement('div');
                    card.className = 'card';
                    
                    // Left Section
                    const leftSection = document.createElement('div');
                    leftSection.className = 'left-section';
                    
                    const metaRow = document.createElement('div');
                    metaRow.className = 'meta-row';
                    metaRow.innerHTML = `
                        <span class="badge" style="background-color: ${{item.badge.bg}}; color: ${{item.badge.color}}">${{item.badge.text}}</span>
                        <span class="date">${{item.date}}</span>
                    `;
                    
                    const keywordRow = document.createElement('div');
                    keywordRow.className = 'keyword-row';
                    keywordRow.title = "클릭하여 복사";
                    keywordRow.onclick = () => copyText(item.keyword, index);
                    
                    keywordRow.innerHTML = `
                        <span class="keyword">${{item.keyword}}</span>
                        <button id="btn-${{index}}" class="copy-btn" title="복사">${{COPY_ICON}}</button>
                    `;
                    
                    leftSection.appendChild(metaRow);
                    leftSection.appendChild(keywordRow);
                    
                    // Right Section
                    const metricsGrid = document.createElement('div');
                    metricsGrid.className = 'metrics-grid';
                    metricsGrid.innerHTML = `
                        <div class="metric"><span class="metric-label">PC</span><span class="metric-value" style="color:#666">${{item.metrics.pc}}</span></div>
                        <div class="metric"><span class="metric-label">모바일</span><span class="metric-value" style="color:#666">${{item.metrics.mobile}}</span></div>
                        <div class="metric"><span class="metric-label">월간 조회</span><span class="metric-value">${{item.metrics.total}}</span></div>
                        <div class="metric"><span class="metric-label">월간 발행</span><span class="metric-value">${{item.metrics.docs}}</span></div>
                        <div class="metric"><span class="metric-label">경쟁률</span><span class="metric-value comp">${{item.metrics.comp}}</span></div>
                    `;
                    
                    card.appendChild(leftSection);
                    card.appendChild(metricsGrid);
                    container.appendChild(card);
                }});

                function copyText(text, index) {{
                    const btn = document.getElementById(`btn-${{index}}`);
                    
                    // Fallback Copy Logic
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    textArea.style.position = "fixed"; 
                    textArea.style.left = "-9999px";
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    
                    try {{
                        const successful = document.execCommand('copy');
                        if (successful) showSuccess(btn);
                        else showFail(text);
                    }} catch (err) {{
                        showFail(text);
                    }}
                    document.body.removeChild(textArea);
                }}

                function showSuccess(btn) {{
                    // Store original icon if needed, or just hardcode swap
                    btn.innerHTML = CHECK_ICON;
                    btn.classList.add('success');
                    
                    setTimeout(() => {{
                        btn.innerHTML = COPY_ICON;
                        btn.classList.remove('success');
                    }}, 2000);
                }}
                
                function showFail(text) {{
                    alert('복사 실패. 브라우저 보안 설정 확인 필요.');
                }}
            </script>
        </body>
        </html>
        """
        
        # Render the Unified Component
        # Height Calculation: Reduced height per card due to thinner layout
        # Approx 100px per card + padding
        total_height = len(component_data) * 110 + 50
        components.html(component_html, height=total_height, scrolling=False)
            
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
