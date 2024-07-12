import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go

def app_single_stock():
    
    pd.set_option('future.no_silent_downcasting', True)

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
    
    
    # Yahoo Finance에서 주식 데이터 가져오기
    def get_stock_data(ticker):
        stock = yf.Ticker(ticker)
        data = stock.history(period="max")
        data.index = pd.to_datetime(data.index)  # 인덱스를 datetime으로 변환
        data.reset_index(inplace=True)  # 인덱스를 열로 변환
        return data

    # CAGR (Compound Annual Growth Rate) 함수
    def cagr(day, a, b):
        return a * (1 + b) ** day

    # Annualized return 계산 및 fitting 함수
    def annualized_return(df, value_column):
        df['Elapsed_Days'] = (df['Date'] - df['Date'].min()).dt.days
        initial_a = df[value_column].iloc[0]
        initial_b = 0.0001
        popt, _ = curve_fit(cagr, df['Elapsed_Days'], df[value_column], p0=[initial_a, initial_b])
        a, b = popt
        df['Fitted_' + value_column] = cagr(df['Elapsed_Days'], a, b)
        return a, b

    # 주식 데이터 drawdown 계산 함수
    def calculate_drawdown(data):
        data['Drawdown'] = (data['Close'] / data['Close'].cummax()) - 1
        return data

    # 배당금 및 CAGR 곡선 시각화 함수
    def plot_dividends_and_cagr(data):
        # 배당금이 0이 아닌 값에 대해 CAGR curve fitting
        non_zero_dividends = data[data['Dividends'] > 0]
        elapsed_days = (non_zero_dividends['Date'] - non_zero_dividends['Date'].min()).dt.days
        initial_a = non_zero_dividends['Dividends'].iloc[0]
        initial_b = 0.0001
        popt, _ = curve_fit(cagr, elapsed_days, non_zero_dividends['Dividends'], p0=[initial_a, initial_b])
        a, b = popt
        non_zero_dividends['Fitted_Dividends'] = cagr(elapsed_days, a, b)
        
        # 배당금 bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(x=data['Date'], y=data['Dividends'], name='Dividends'))
        
        # CAGR 곡선
        fig.add_trace(go.Scatter(x=non_zero_dividends['Date'], y=non_zero_dividends['Fitted_Dividends'], mode='lines', name='CAGR Fit', line=dict(color='red', dash='dot')))
        
        # Annual return 계산
        annual_return = (1 + b) ** 365.25 - 1
        
        # Annotation 추가
        x_middle = non_zero_dividends['Date'].iloc[len(non_zero_dividends) // 2]  # x의 중앙값
        y_middle = non_zero_dividends['Fitted_Dividends'].iloc[len(non_zero_dividends) // 2]  # y의 중앙값
        y_range = non_zero_dividends['Fitted_Dividends'].max() - non_zero_dividends['Fitted_Dividends'].min()
        y_middle = y_middle + 0.1 * y_range

        fig.add_annotation(x=x_middle, y=y_middle, text=f"Annual Return: {annual_return:.2%}", showarrow=False, font=dict(size=12, color="black"), align='center')
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title="Dividends and CAGR Fit",
            xaxis_title="Date",
            yaxis_title="Dividends",
            legend=dict(x=0, y=1, xanchor='left', yanchor='top')
        )
        
        return fig


    # 주가 데이터 시각화
    def plot_stock_data(data, a, b, ticker):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines', name='Actual Stock Price', line=dict(color='black')))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Fitted_Close'], mode='lines', name='Fitted Model', line=dict(color='red', dash='dot')))
        annual_return = (1 + b) ** 365.25 - 1
        x_middle = data['Date'].iloc[len(data) // 2]  # x의 중앙값
        y_middle = data['Fitted_Close'].iloc[len(data) // 2]   # y의 중앙값
        y_range = data['Fitted_Close'].max() - data['Fitted_Close'].min()
        y_middle = y_middle + 0.1 * y_range

        fig.add_annotation(x=x_middle, y=y_middle, text=f"Annual Return: {annual_return:.2%}", showarrow=False, font=dict(size=12, color="black"), align='center')
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title=f"{ticker} Stock Price",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            legend=dict(x=0, y=1, xanchor='left', yanchor='top')
        )
        return fig

    # Drawdown 그래프 시각화
    def plot_drawdown(data, ticker):
        drawdown_data = calculate_drawdown(data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=drawdown_data['Date'], y=drawdown_data['Drawdown'] * 100, mode='lines', name='Drawdown', line=dict(color='gray', width=2)))
        fig.add_trace(go.Scatter(x=drawdown_data['Date'], y=drawdown_data['Drawdown'] * 100, mode='lines', name='Drawdown', fill='tozeroy', line=dict(color='gray', width=1)))
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title=f"{ticker} Drawdown",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            showlegend=False
        )
        return fig

    # Streamlit 애플리케이션 실행
    st.title("Stock Price Visualization and Analysis")

    # 사용자 입력 받기
    ticker = st.text_input("Enter a stock ticker symbol:")

    if st.button('Submit'):
        try:
            # 주식 데이터 가져오기 및 시각화
            stock_data = get_stock_data(ticker)
            
            if stock_data.empty:
                st.error("No data found for the entered ticker symbol. Please check the symbol and try again.")
            else:
                # yfinance의 Dividends 데이터 사용
                stock_data['Dividends'] = stock_data['Dividends']

                # Annualized return 계산
                a, b = annualized_return(stock_data, 'Close')

                # 주가 및 drawdown 그래프 표시
                price_plot = plot_stock_data(stock_data, a, b, ticker)
                drawdown_plot = plot_drawdown(stock_data, ticker)
                dividend_plot = plot_dividends_and_cagr(stock_data)

                # 주가 및 drawdown 그래프 표시
                st.plotly_chart(price_plot, use_container_width=True)
                st.plotly_chart(drawdown_plot, use_container_width=True)
                st.plotly_chart(dividend_plot, use_container_width=True)

        except Exception as e:
            st.error(f"An error occurred: {e}. Please check the ticker symbol and try again.")
