import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go
from datetime import datetime

def app_single_stock():
    pd.set_option('future.no_silent_downcasting', True)

    st.markdown(
        """
        <style>
        .reportview-container {background: white;}
        .main .block-container {background:white;}
        </style>
        """,
        unsafe_allow_html=True
    )

    def get_stock_data(ticker):
        stock = yf.Ticker(ticker)
        data = stock.history(period="max")
        data.index = pd.to_datetime(data.index)
        data.reset_index(inplace=True)
        data['Date'] = pd.to_datetime(data['Date'])
        return data

    def get_sp500_data():
        sp500 = yf.Ticker("^GSPC")
        sp500_data = sp500.history(period="max")
        sp500_data.index = pd.to_datetime(sp500_data.index)
        sp500_data.reset_index(inplace=True)
        sp500_data['Date'] = pd.to_datetime(sp500_data['Date'])
        return sp500_data


    def cagr(day, a, b):
        return a * (1 + b) ** day

    def annualized_return(df, value_column):
        df['Elapsed_Days'] = (df['Date'] - df['Date'].min()).dt.days
        initial_a = df[value_column].iloc[0]
        initial_b = 0.0001
        popt, _ = curve_fit(cagr, df['Elapsed_Days'], df[value_column], p0=[initial_a, initial_b])
        a, b = popt
        df['Fitted_' + value_column] = cagr(df['Elapsed_Days'], a, b)
        return a, b

    def calculate_drawdown(data):
        data['Drawdown'] = (data['Close'] / data['Close'].cummax()) - 1
        return data

    def plot_dividends_and_cagr(data):
        non_zero_dividends = data[data['Dividends'] > 0]
        if non_zero_dividends.empty:
            st.warning("입력된 티커 기호에 대한 배당금 데이터가 없습니다.")
            return None

        elapsed_days = (non_zero_dividends['Date'] - non_zero_dividends['Date'].min()).dt.days
        initial_a = non_zero_dividends['Dividends'].iloc[0]
        initial_b = 0.0001
        popt, _ = curve_fit(cagr, elapsed_days, non_zero_dividends['Dividends'], p0=[initial_a, initial_b])
        a, b = popt
        non_zero_dividends['Fitted_Dividends'] = cagr(elapsed_days, a, b)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=data['Date'], y=data['Dividends'], name='배당금'))
        fig.add_trace(go.Scatter(x=non_zero_dividends['Date'], y=non_zero_dividends['Fitted_Dividends'], mode='lines', name='CAGR 피팅', line=dict(color='red', dash='dot')))
        annual_return = (1 + b) ** 365.25 - 1

        x_middle = non_zero_dividends['Date'].iloc[len(non_zero_dividends) // 2]
        y_middle = non_zero_dividends['Fitted_Dividends'].iloc[len(non_zero_dividends) // 2]
        y_range = non_zero_dividends['Fitted_Dividends'].max() - non_zero_dividends['Fitted_Dividends'].min()
        y_middle = y_middle + 0.2 * y_range

        fig.add_annotation(x=x_middle, y=y_middle, text=f"연평균 상승률: {annual_return:.2%}", showarrow=False, font=dict(size=12, color="red"), align='center')
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title="배당금 및 CAGR 피팅",
            xaxis_title="날짜",
            yaxis_title="배당금",
            legend=dict(x=0, y=1, xanchor='left', yanchor='top')
        )
        return fig

    def plot_stock_data(data, a, b, ticker, yaxis_type='linear'):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines', name='실제 주가', line=dict(color='black')))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Fitted_Close'], mode='lines', name='CAGR 피팅', line=dict(color='red', dash='dot')))
        annual_return = (1 + b) ** 365.25 - 1

        x_middle = data['Date'].iloc[len(data) // 2]
        y_middle = data['Fitted_Close'].iloc[len(data) // 2]
        y_range = data['Fitted_Close'].max() - data['Fitted_Close'].min()
        y_middle = y_middle + 0.2 * y_range

        if yaxis_type == 'log':
            y_min = max(data['Close'].min(), 1e-6)  # 로그 스케일을 위한 최소값 설정
            y_max = data['Close'].max()
            y_middle = 10 ** ((np.log10(data['Fitted_Close'].min()) + np.log10(data['Fitted_Close'].max())) / 2 + 0.2 * (np.log10(data['Fitted_Close'].max()) - np.log10(data['Fitted_Close'].min())))  # 로그 스케일에 맞춘 y_middle 값
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot', type='log', range=[np.log10(y_min), np.log10(y_max)])
        else:
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot', type=yaxis_type)
        
        fig.add_annotation(x=x_middle, y=y_middle, text=f"연평균 상승률: {annual_return:.2%}", showarrow=False, font=dict(size=12, color="red"), align='center')
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')

        fig.update_layout(
            title=f"{ticker} 주가",
            xaxis_title="날짜",
            yaxis_title="가격 (USD)",
            legend=dict(x=0, y=1, xanchor='left', yanchor='top')
        )
        return fig

    def plot_drawdown(data, ticker):
        drawdown_data = calculate_drawdown(data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=drawdown_data['Date'], y=drawdown_data['Drawdown'] * 100, mode='lines', name='최대 낙폭', line=dict(color='gray', width=2)))
        fig.add_trace(go.Scatter(x=drawdown_data['Date'], y=drawdown_data['Drawdown'] * 100, mode='lines', name='최대 낙폭', fill='tozeroy', line=dict(color='gray', width=1)))
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title=f"{ticker} 최대 낙폭",
            xaxis_title="날짜",
            yaxis_title="최대 낙폭 (%)",
            showlegend=False
        )
        return fig
    
    def plot_inverted_stock_data(data, ticker, yaxis_type='linear'):
        # 상하 반전된 데이터 생성
        data['Inverted_Close'] = -data['Close'] + data['Close'].max() + data['Close'].min()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Inverted_Close'], mode='lines', name='상하 반전 주가', line=dict(color='blue')))
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title=f"{ticker} 상하 반전 주가",
            xaxis_title="날짜",
            yaxis_title="가격 (Arbitary Unit)",
            legend=dict(x=0, y=1, xanchor='left', yanchor='top')
        )
        
        if yaxis_type == 'log':
            y_min = max(data['Inverted_Close'].min(), 1e-6)  # 로그 스케일을 위한 최소값 설정
            y_max = data['Inverted_Close'].max()
            fig.update_yaxes(type='log', range=[np.log10(y_min), np.log10(y_max)])
    
        return fig




    st.title("개별 주식 분석")

    ticker = st.text_input("주식 티커 기호를 입력하세요:")

    with st.expander("예시 티커 보기"):
        st.markdown(
            """
            <table>
                <tr><th>지수/종목</th><th>티커</th><th>비고</th></tr>
                <tr><td>다우존스</td><td>^DJI</td><td>지수</td></tr>
                <tr><td>S&P500</td><td>^GSPC</td><td>지수</td></tr>
                <tr><td>나스닥100</td><td>^NDX</td><td>지수</td></tr>
                <tr><td>SPY ETF</td><td>SPY</td><td>ETF</td></tr>
                <tr><td>마이크로소프트</td><td>MSFT</td><td>미국주식</td></tr>
                <tr><td>애플</td><td>AAPL</td><td>미국주식</td></tr>
                <tr><td>삼성전자</td><td>005930.KS</td><td>코스피</td></tr>
                <tr><td>리노공업</td><td>058470.KQ</td><td>코스닥</td></tr>
            </table>
            """,
            unsafe_allow_html=True
        )

    scale_option = st.radio("가격 축 스케일을 선택하세요", ('Linear', 'Logarithmic'))

    submit_button = st.button('show')

    if 'stock_data' not in st.session_state:
        st.session_state.stock_data = None
    if 'filtered_data' not in st.session_state:
        st.session_state.filtered_data = None
    if 'start_date' not in st.session_state:
        st.session_state.start_date = None
    if 'end_date' not in st.session_state:
        st.session_state.end_date = None
    if 'initial_submit' not in st.session_state:
        st.session_state.initial_submit = False

    if submit_button and ticker:
        try:
            stock_data = get_stock_data(ticker)
            # S&P 500 데이터를 불러옴
            sp500_data = get_sp500_data()

            # 주식 데이터와 S&P 500 데이터를 주식의 시작 날짜부터 필터링
            start_date = stock_data['Date'].min()
            sp500_data = sp500_data[sp500_data['Date'] >= start_date].copy()

            # 두 데이터가 같은 날짜를 기준으로 매칭되도록 결합
            merged_data = pd.merge(stock_data[['Date', 'Close']], sp500_data[['Date', 'Close']], on='Date', suffixes=('_Stock', '_SP500'))

            # 주가를 S&P 500 지수로 나눈 값을 구하고, 초기값으로 스케일링
            merged_data['Relative_Performance'] = merged_data['Close_Stock'] / merged_data['Close_SP500']
            merged_data['Scaled_Relative_Performance'] = merged_data['Relative_Performance'] / merged_data['Relative_Performance'].iloc[0]


            if stock_data.empty:
                st.error("입력된 티커 기호에 대한 데이터를 찾을 수 없습니다. 기호를 확인하고 다시 시도하세요.")
            else:
                st.session_state.stock_data = stock_data
                st.session_state.filtered_data = stock_data
                st.session_state.start_date = stock_data['Date'].min()
                st.session_state.end_date = stock_data['Date'].max()
                st.session_state.initial_submit = True

                stock_data['Dividends'] = stock_data['Dividends']
                a, b = annualized_return(stock_data, 'Close')

                yaxis_type = 'log' if scale_option == 'Logarithmic' else 'linear'
                price_plot = plot_stock_data(stock_data, a, b, ticker, yaxis_type)
                drawdown_plot = plot_drawdown(stock_data, ticker)

                st.plotly_chart(price_plot, use_container_width=True)
                st.plotly_chart(drawdown_plot, use_container_width=True)
                # 주식의 S&P 500 대비 상대 성과를 시각화하는 그래프 생성
                fig = go.Figure()

                # 상대 성과 데이터 추가
                fig.add_trace(go.Scatter(x=merged_data['Date'], y=merged_data['Scaled_Relative_Performance'], mode='lines', name=f'{ticker} / S&P 500', line=dict(color='purple')))

                # 그래프 레이아웃 설정
                fig.update_layout(
                    title=f"{ticker} / S&P 500 상대 성과",
                    xaxis_title="날짜",
                    yaxis_title="상대 성과 (초기값 = 1)",
                    legend=dict(x=0, y=1, xanchor='left', yanchor='top')

                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')

                # 그래프 출력
                st.plotly_chart(fig, use_container_width=True)




                dividend_plot = plot_dividends_and_cagr(stock_data)
                if dividend_plot:
                    st.plotly_chart(dividend_plot, use_container_width=True)
                
                st.plotly_chart(plot_inverted_stock_data(stock_data, ticker), use_container_width=True)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}. 티커 기호를 확인하고 다시 시도하세요.")

    if st.session_state.initial_submit and st.session_state.stock_data is not None:
        min_date = st.session_state.stock_data['Date'].min()
        max_date = st.session_state.stock_data['Date'].max()
        st.subheader("날짜 범위 조정")
        start_date, end_date = st.slider(
            "날짜 범위를 선택하세요",
            min_value=min_date.to_pydatetime(),
            max_value=max_date.to_pydatetime(),
            value=(st.session_state.start_date.to_pydatetime(), st.session_state.end_date.to_pydatetime()),
            format="YYYY-MM-DD"
        )

        submit_range_button = st.button('날짜 범위 분석')

        if submit_range_button:
            st.session_state.start_date = pd.to_datetime(start_date)
            st.session_state.end_date = pd.to_datetime(end_date)
            st.session_state.filtered_data = st.session_state.stock_data[(st.session_state.stock_data['Date'] >= st.session_state.start_date) & (st.session_state.stock_data['Date'] <= st.session_state.end_date)]

            a, b = annualized_return(st.session_state.filtered_data, 'Close')

            yaxis_type = 'log' if scale_option == 'Logarithmic' else 'linear'
            price_plot = plot_stock_data(st.session_state.filtered_data, a, b, ticker, yaxis_type)
            drawdown_plot = plot_drawdown(st.session_state.filtered_data, ticker)

            st.plotly_chart(price_plot, use_container_width=True)
            st.plotly_chart(drawdown_plot, use_container_width=True)

            dividend_plot = plot_dividends_and_cagr(st.session_state.filtered_data)
            if dividend_plot:
                st.plotly_chart(dividend_plot, use_container_width=True)

            st.plotly_chart(plot_inverted_stock_data(st.session_state.filtered_data, ticker), use_container_width=True)
