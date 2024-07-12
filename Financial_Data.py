import streamlit as st
from app_single_stock import app_single_stock as single_stock_app
from app_financial_data import app_financial_data as financial_data_app
from app_home import app as home_app

PAGES = {
    "Home": home_app,
    "Single Stock Analysis": single_stock_app,
    "Financial Data Analysis": financial_data_app
}

if 'page' not in st.session_state:
    st.session_state.page = "Home"

def set_page(page):
    st.session_state.page = page

# Custom CSS to style the sidebar and add a top navigation bar
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

# Add top navigation bar
st.markdown('<div class="top-nav">', unsafe_allow_html=True)

nav_buttons = ["Home", "Single Stock Analysis", "Financial Data Analysis"]

for page in nav_buttons:
    if st.button(page):
        set_page(page)

st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.page))

page = PAGES[selection]
page()
