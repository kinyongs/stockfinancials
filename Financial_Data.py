import streamlit as st
import streamlit.components.v1 as components

# 각 페이지를 정의한 딕셔너리
from app_single_stock import app_single_stock as single_stock_app
from app_financial_data import app_financial_data as financial_data_app
from app_double_stock import app_double_stock as double_stock_app
from app_home import app as home_app
from app_sp500 import app_sp500 as sp500_app
from app_Summary import app_Summary as summary_app
from app_Monthly_Investment import app_Monthly_Investment as Monthly_Investment_app
from app_stock_value import app_stock_value as stock_value_app
from app_stock_value2 import app_stock_value2 as stock_value_app2
from app_stock_DCA import app_stock_DCA as stock_DCA_app

PAGES = {
    "홈": home_app,
    "S&P 500 최근 자료 요약": summary_app,
    "S&P 500과 매크로 데이터 분석": sp500_app,
    "=============break1=================": home_app,
    "개별 주식 분석": single_stock_app,
    "주가 비교 분석": double_stock_app,
    "기업 적정 주가 추정(FCF 기반)":stock_value_app,
    "기업 적정 주가 추정(ROE 기반)":stock_value_app2,
    "기업 재무 데이터 분석": financial_data_app,
    "적립식 투자 시뮬레이션(주가 기반)" : stock_DCA_app,
    "=============break2==================": home_app, 
    "적립식 투자 시뮬레이션(일반)": Monthly_Investment_app
}

# 드롭다운 메뉴를 이용한 네비게이션
selected_page = st.selectbox("페이지 선택", options=list(PAGES.keys()))

# 선택된 페이지 로드
page = PAGES[selected_page]
page()

components.html(
    """
    <!-- Global site tag (gtag.js) - Google Analytics -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3899080320104517"
     crossorigin="anonymous"></script>
    """
)