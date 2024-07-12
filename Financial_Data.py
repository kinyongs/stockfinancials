import streamlit as st
from app_single_stock import app_single_stock as single_stock_app
from app_financial_data import app_financial_data as financial_data_app
from app_home import app as home_app

PAGES = {
    "Home": home_app,
    "Single Stock Analysis": single_stock_app,
    "Financial Data Analysis": financial_data_app
}

st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

page = PAGES[selection]
page()
