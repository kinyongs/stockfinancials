import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go

def app_double_stock():
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

    def plot_dividends_and_cagr(data1, data2, ticker1, ticker2):
        non_zero_dividends1 = data1[data1['Dividends'] > 0]
        non_zero_dividends2 = data2[data2['Dividends'] > 0]

        fig = go.Figure()

        if not non_zero_dividends1.empty:
            elapsed_days1 = (non_zero_dividends1['Date'] - non_zero_dividends1['Date'].min()).dt.days
            initial_a1 = non_zero_dividends1['Dividends'].iloc[0]
            initial_b1 = 0.0001
            popt1, _ = curve_fit(cagr, elapsed_days1, non_zero_dividends1['Dividends'], p0=[initial_a1, initial_b1])
            a1, b1 = popt1
            non_zero_dividends1['Fitted_Dividends'] = cagr(elapsed_days1, a1, b1)
            fig.add_trace(go.Bar(x=data1['Date'], y=data1['Dividends'], name=f'{ticker1} 배당금'))
            fig.add_trace(go.Scatter(x=non_zero_dividends1['Date'], y=non_zero_dividends1['Fitted_Dividends'], mode='lines', name=f'{ticker1} CAGR 피팅', line=dict(color='blue', dash='dot')))
            annual_return1 = (1 + b1) ** 365.25 - 1

            x_middle1 = non_zero_dividends1['Date'].iloc[len(non_zero_dividends1) // 2]
            y_middle1 = non_zero_dividends1['Fitted_Dividends'].iloc[len(non_zero_dividends1) // 2]
            y_range1 = non_zero_dividends1['Fitted_Dividends'].max() - non_zero_dividends1['Fitted_Dividends'].min()
            y_middle1 = y_middle1 + 0.2 * y_range1

            fig.add_annotation(x=x_middle1, y=y_middle1, text=f"{ticker1} 연간 배당률: {annual_return1:.2%}", showarrow=False, font=dict(size=12, color="blue"), align='center')
        else:
            st.warning(f"{ticker1}에 대한 배당금 데이터가 없습니다.")

        if not non_zero_dividends2.empty:
            elapsed_days2 = (non_zero_dividends2['Date'] - non_zero_dividends2['Date'].min()).dt.days
            initial_a2 = non_zero_dividends2['Dividends'].iloc[0]
            initial_b2 = 0.0001
            popt2, _ = curve_fit(cagr, elapsed_days2, non_zero_dividends2['Dividends'], p0=[initial_a2, initial_b2])
            a2, b2 = popt2
            non_zero_dividends2['Fitted_Dividends'] = cagr(elapsed_days2, a2, b2)
            fig.add_trace(go.Bar(x=data2['Date'], y=data2['Dividends'], name=f'{ticker2} 배당금'))
            fig.add_trace(go.Scatter(x=non_zero_dividends2['Date'], y=non_zero_dividends2['Fitted_Dividends'], mode='lines', name=f'{ticker2} CAGR 피팅', line=dict(color='red', dash='dot')))
            annual_return2 = (1 + b2) ** 365.25 - 1

            x_middle2 = non_zero_dividends2['Date'].iloc[len(non_zero_dividends2) // 2]
            y_middle2 = non_zero_dividends2['Fitted_Dividends'].iloc[len(non_zero_dividends2) // 2]
            y_range2 = non_zero_dividends2['Fitted_Dividends'].max() - non_zero_dividends2['Fitted_Dividends'].min()
            y_middle2 = y_middle2 + 0.2 * y_range2

            fig.add_annotation(x=x_middle2, y=y_middle2, text=f"{ticker2} 연간 배당률: {annual_return2:.2%}", showarrow=False, font=dict(size=12, color="red"), align='center')
        else:
            st.warning(f"{ticker2}에 대한 배당금 데이터가 없습니다.")

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title="배당금 및 CAGR 피팅",
            xaxis_title="날짜",
            yaxis_title="배당금",
            legend=dict(x=0, y=1, xanchor='left', yanchor='top')
        )
        return fig


    def plot_stock_data(data1, data2, ticker1, ticker2):
        fig = go.Figure()

        a1, b1 = annualized_return(data1, 'Close')
        a2, b2 = annualized_return(data2, 'Close')

        fig.add_trace(go.Scatter(x=data1['Date'], y=data1['Close'], mode='lines', name=f'{ticker1} 실제 주가', line=dict(color='black')))
        fig.add_trace(go.Scatter(x=data1['Date'], y=data1['Fitted_Close'], mode='lines', name=f'{ticker1} CAGR 피팅', line=dict(color='red', dash='dot')))
        fig.add_trace(go.Scatter(x=data2['Date'], y=data2['Close'], mode='lines', name=f'{ticker2} 실제 주가', line=dict(color='gray')))
        fig.add_trace(go.Scatter(x=data2['Date'], y=data2['Fitted_Close'], mode='lines', name=f'{ticker2} CAGR 피팅', line=dict(color='blue', dash='dot')))

        annual_return1 = (1 + b1) ** 365.25 - 1
        annual_return2 = (1 + b2) ** 365.25 - 1

        fig.add_annotation(x=data1['Date'].iloc[len(data1) // 2], y=data1['Fitted_Close'].iloc[len(data1) // 2], text=f"{ticker1} 연간 수익률: {annual_return1:.2%}", showarrow=False, font=dict(size=12, color="red"), align='center')
        fig.add_annotation(x=data2['Date'].iloc[len(data2) // 2], y=data2['Fitted_Close'].iloc[len(data2) // 2], text=f"{ticker2} 연간 수익률: {annual_return2:.2%}", showarrow=False, font=dict(size=12, color="blue"), align='center')

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title="주가 비교",
            xaxis_title="날짜",
            yaxis_title="가격 (USD)",
            legend=dict(x=0, y=1, xanchor='left', yanchor='top')
        )
        return fig

    def plot_drawdown(data1, data2, ticker1, ticker2):
        drawdown1 = calculate_drawdown(data1)
        drawdown2 = calculate_drawdown(data2)
        
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=drawdown1['Date'], y=drawdown1['Drawdown'] * 100, mode='lines', name=f'{ticker1} 최대 낙폭', line=dict(color='black')))
        fig.add_trace(go.Scatter(x=drawdown2['Date'], y=drawdown2['Drawdown'] * 100, mode='lines', name=f'{ticker2} 최대 낙폭', line=dict(color='gray')))
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', griddash='dot')
        fig.update_layout(
            title="최대 낙폭 비교",
            xaxis_title="날짜",
            yaxis_title="최대 낙폭 (%)",
            showlegend=True,
            legend=dict(x=0, y=1, xanchor='left', yanchor='bottom')
        )
        return fig

    st.title("두 주식 분석 및 비교")

    ticker1 = st.text_input("첫 번째 주식 티커 기호를 입력하세요:")
    ticker2 = st.text_input("두 번째 주식 티커 기호를 입력하세요:")

    submit_button = st.button('show')

    if 'stock_data1' not in st.session_state:
        st.session_state.stock_data1 = None
    if 'stock_data2' not in st.session_state:
        st.session_state.stock_data2 = None
    if 'filtered_data1' not in st.session_state:
        st.session_state.filtered_data1 = None
    if 'filtered_data2' not in st.session_state:
        st.session_state.filtered_data2 = None
    if 'start_date' not in st.session_state:
        st.session_state.start_date = None
    if 'end_date' not in st.session_state:
        st.session_state.end_date = None
    if 'initial_submit' not in st.session_state:
        st.session_state.initial_submit = False

    if submit_button and ticker1 and ticker2:
        try:
            stock_data1 = get_stock_data(ticker1)
            stock_data2 = get_stock_data(ticker2)
            if stock_data1.empty or stock_data2.empty:
                st.error("입력된 티커 기호에 대한 데이터를 찾을 수 없습니다. 기호를 확인하고 다시 시도하세요.")
            else:
                st.session_state.stock_data1 = stock_data1
                st.session_state.stock_data2 = stock_data2
                st.session_state.filtered_data1 = stock_data1
                st.session_state.filtered_data2 = stock_data2
                st.session_state.start_date = max(stock_data1['Date'].min(), stock_data2['Date'].min())
                st.session_state.end_date = min(stock_data1['Date'].max(), stock_data2['Date'].max())
                st.session_state.initial_submit = True

                stock_plot = plot_stock_data(stock_data1, stock_data2, ticker1, ticker2)
                drawdown_plot = plot_drawdown(stock_data1, stock_data2, ticker1, ticker2)
                dividend_plot = plot_dividends_and_cagr(stock_data1, stock_data2, ticker1, ticker2)

                st.plotly_chart(stock_plot, use_container_width=True)
                st.plotly_chart(drawdown_plot, use_container_width=True)
                st.plotly_chart(dividend_plot, use_container_width=True)
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}. 티커 기호를 확인하고 다시 시도하세요.")

    if st.session_state.initial_submit and st.session_state.stock_data1 is not None and st.session_state.stock_data2 is not None:
        min_date = max(st.session_state.stock_data1['Date'].min(), st.session_state.stock_data2['Date'].min())
        max_date = min(st.session_state.stock_data1['Date'].max(), st.session_state.stock_data2['Date'].max())

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
            st.session_state.filtered_data1 = st.session_state.stock_data1[
                (st.session_state.stock_data1['Date'] >= st.session_state.start_date) & 
                (st.session_state.stock_data1['Date'] <= st.session_state.end_date)
            ]
            st.session_state.filtered_data2 = st.session_state.stock_data2[
                (st.session_state.stock_data2['Date'] >= st.session_state.start_date) & 
                (st.session_state.stock_data2['Date'] <= st.session_state.end_date)
            ]

            stock_plot = plot_stock_data(st.session_state.filtered_data1, st.session_state.filtered_data2, ticker1, ticker2)
            drawdown_plot = plot_drawdown(st.session_state.filtered_data1, st.session_state.filtered_data2, ticker1, ticker2)
            dividend_plot = plot_dividends_and_cagr(st.session_state.filtered_data1, st.session_state.filtered_data2, ticker1, ticker2)

            st.plotly_chart(stock_plot, use_container_width=True)
            st.plotly_chart(drawdown_plot, use_container_width=True)
            st.plotly_chart(dividend_plot, use_container_width=True)

if __name__ == '__main__':
    app_double_stock()
