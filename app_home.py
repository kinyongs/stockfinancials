# app_home.py

import streamlit as st

def app():

    # 배경 색깔 지정
    st.markdown(
        """
        <style>
        .reportview-container {background: white;}
        .main .block-container {background:white;}
        </style>
        """,
        unsafe_allow_html=True
    )

    
    st.title('홈')
    st.write('홈 페이지에 오신 것을 환영합니다.')
    st.markdown("[운영자의 블로그 : https://blog.naver.com/smartdotori](https://blog.naver.com/smartdotori)")

    st.header('S&P 500과 매크로 데이터 분석')
    st.write('S&P 500 Index와 CAGR fitting curve, drawdown, 연간 수익률을 제공합니다.')
    st.write('EPS, M2, GDP, 10년물 금리, 실업률 정보를 S&P 500 지수와 함께 제시합니다.')

    st.header('개별 주식 분석')
    st.write('개별 주식 분석 페이지는 주식 및 ETF 가격, 최대 낙폭, 배당금에 대한 정보를 제공합니다.')
    st.write('개별 주식에 대한 연평균 상승 추세선을 계산합니다.')

    st.header('주가 비교 분석')
    st.write('주가 비교 분석 페이지는 2개의 주식 및 ETF에 대하여, 주가, 최대 낙폭, 배당금에 대한 정보를 비교합니다.')
    st.write('개별 주식에 대한 연평균 상승 추세선을 계산합니다.')

    st.header('기업 재무 데이터 분석')
    st.write('재무 데이터 분석 페이지는 기업의 재무 정보를 제공합니다.')
    st.write(' 또한 오너 어닝 및 목표 주가를 제시합니다.')

    