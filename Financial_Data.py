import streamlit as st
from app_single_stock import app_single_stock as single_stock_app
from app_financial_data import app_financial_data as financial_data_app
from app_home import app as home_app

PAGES = {
    "홈": home_app,
    "개별 주식 분석": single_stock_app,
    "금융 데이터 분석": financial_data_app
}

if 'page' not in st.session_state:
    st.session_state.page = "홈"

def set_page(page):
    st.session_state.page = page

# 사이드바와 상단 네비게이션 바를 스타일링하기 위한 커스텀 CSS
st.markdown("""
    <style>
    .top-nav {
        background-color: #f8f9fa;
        padding: 10px;
        text-align: center;
        border-bottom: 1px solid #e0e0e0;
    }
    .top-nav button {
        margin: 0 5px;  /* 최소 간격을 위해 5px로 설정 */
        background: #007bff;  /* 버튼 배경색 */
        border: none;
        color: white;  /* 버튼 텍스트 색상 */
        font-size: 1rem;
        cursor: pointer;
        padding: 10px 20px;
        border-radius: 5px;  /* 버튼의 모서리를 둥글게 */
        transition: background-color 0.3s ease;  /* 호버 효과를 위한 전환 */
    }
    .top-nav button:hover {
        background: #0056b3;  /* 호버 시의 배경색 */
    }
    </style>
    """, unsafe_allow_html=True)

# 상단 네비게이션 바 추가
st.markdown('<div class="top-nav">', unsafe_allow_html=True)

nav_buttons = ["홈", "개별 주식 분석", "금융 데이터 분석"]

for page in nav_buttons:
    if st.button(page):
        set_page(page)

st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.title('네비게이션')
selection = st.sidebar.radio("이동", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.page))

page = PAGES[selection]
page()
