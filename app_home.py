# app_home.py

import streamlit as st

def app():

    #background 색깔 지정
    st.markdown(
        """
        <style>
        .reportview-container {background: white;}
        .main .block-container {background:white;}
        </style>
        """,
        unsafe_allow_html=True
    )

    
    st.title('Home')
    st.write('Welcome to the Home page. Use the sidebar to navigate to different pages.')

    st.header('Single Stock Analysis')
    st.write('The Single Stock Analysis page provides information on stock and ETF prices, drawdown, and dividends. It calculates the annual average uptrend line for these assets.')

    st.header('Financial Data Analysis')
    st.write('The Financial Data Analysis page provides financial information of companies. It also includes Owner Earnings and Target Price.')
