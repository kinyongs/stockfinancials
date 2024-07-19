import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 방문자 데이터를 저장할 CSV 파일 경로
CSV_FILE_PATH = 'visitor_count.csv'

# 방문자 데이터를 로드하는 함수
def load_visitor_data():
    try:
        data = pd.read_csv(CSV_FILE_PATH, index_col='date', parse_dates=True)
    except FileNotFoundError:
        data = pd.DataFrame(columns=['daily_count', 'total_count'])
    return data

# 방문자 데이터를 저장하는 함수
def save_visitor_data(data):
    data.to_csv(CSV_FILE_PATH)

# 오늘의 방문자 수를 증가시키는 함수
def increment_visitor_count():
    data = load_visitor_data()
    today = pd.Timestamp(datetime.now().date())

    if today not in data.index:
        daily_count = 1
        if not data.empty:
            total_count = data['total_count'].iloc[-1] + 1
        else:
            total_count = 1
    else:
        daily_count = data.loc[today, 'daily_count'] + 1
        total_count = data.loc[today, 'total_count'] + 1

    data.loc[today, 'daily_count'] = daily_count
    data.loc[today, 'total_count'] = total_count

    save_visitor_data(data)
    return daily_count, total_count

# 방문자 수를 초기화하는 함수 (매일 자정마다 초기화)
def reset_daily_visitor_count():
    data = load_visitor_data()
    today = pd.Timestamp(datetime.now().date())
    yesterday = today - timedelta(days=1)

    if yesterday in data.index and today not in data.index:
        data.loc[today, 'daily_count'] = 0
        save_visitor_data(data)

# 페이지 로드 시 방문자 수 증가
reset_daily_visitor_count()
daily_count, total_count = increment_visitor_count()

# 각 페이지를 정의한 딕셔너리
from app_single_stock import app_single_stock as single_stock_app
from app_financial_data import app_financial_data as financial_data_app
from app_double_stock import app_double_stock as double_stock_app
from app_home import app as home_app

PAGES = {
    "홈": home_app,
    "개별 주식 분석": single_stock_app,
    "주가 비교 분석": double_stock_app,
    "기업 재무 데이터 분석": financial_data_app
}

if 'page' not in st.session_state:
    st.session_state.page = "홈"

def set_page(page):
    st.session_state.page = page

# 사이드바와 상단 네비게이션 바를 스타일링하기 위한 커스텀 CSS
st.markdown("""
    <style>
    .top-nav {
        background-color: #FFFFFF;
        padding: 10px;
        text-align: center;
        border: none;
        display: flex;
        justify-content: center;
        gap: 10px;
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

nav_buttons = ["홈", "개별 주식 분석", "주가 비교 분석","기업 재무 데이터 분석"]

for page in nav_buttons:
    if st.button(page):
        set_page(page)

st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.title('네비게이션')
selection = st.sidebar.radio("이동", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.page))

page = PAGES[selection]
page()

# 방문자 카운터 추가
st.sidebar.markdown("---")
st.sidebar.markdown(f"**오늘 방문자 수:** {daily_count}")
st.sidebar.markdown(f"**누적 방문자 수:** {total_count}")
