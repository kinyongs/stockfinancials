import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go

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
            st.warning("No dividend data available for the entered ticker symbol.")
            return None

        elapsed_days = (non_zero_dividends['Date'] - non_zero_dividends['Date'].min()).dt.days
        initial_a = non_zero_dividends['Dividends'].iloc[0]
        initial_b = 0.0001
        popt, _ = curve_fit(cagr, elapsed_days, non_zero_dividends['Dividends'], p0=[initial_a, initial_b])
        a, b = popt
        non_zero_dividends['Fitted_Dividends'] = cagr(elapsed_days, a, b)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=data['Date'], y=data['Dividends'], name='Dividends'))
        fig.add_trace(go.Scatter(x=non_zero_dividends['Date'], y=non_zero_dividends['Fitted_Dividends'], mode='lines', name='CAGR Fit', line=dict(color='red', dash='dot')))
        annual_return = (1 + b) ** 365.25 - 1

        x_middle = non_zero_dividends['Date'].iloc[len(non_zero_dividends) // 2]
        y_middle = non_zero_dividends['Fitted_Dividends'].iloc[len(non_zero_dividends) // 2]
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

    def plot_stock_data(data, a, b, ticker):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines', name='Actual Stock Price', line=dict(color='black')))
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Fitted_Close'], mode='lines', name='Fitted Model', line=dict(color='red', dash='dot')))
        annual_return = (1 + b) ** 365.25 - 1

        x_middle = data['Date'].iloc[len(data) // 2]
        y_middle = data['Fitted_Close'].iloc[len(data) // 2]
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

    st.title("Stock Price Visualization and Analysis")

    ticker = st.text_input("Enter a stock ticker symbol:")
    submit_button = st.button('Submit')

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
            if stock_data.empty:
                st.error("No data found for the entered ticker symbol. Please check the symbol and try again.")
            else:
                st.session_state.stock_data = stock_data
                st.session_state.filtered_data = stock_data
                st.session_state.start_date = stock_data['Date'].min()
                st.session_state.end_date = stock_data['Date'].max()
                st.session_state.initial_submit = True

                stock_data['Dividends'] = stock_data['Dividends']
                a, b = annualized_return(stock_data, 'Close')

                price_plot = plot_stock_data(stock_data, a, b, ticker)
                drawdown_plot = plot_drawdown(stock_data, ticker)

                st.plotly_chart(price_plot, use_container_width=True)
                st.plotly_chart(drawdown_plot, use_container_width=True)

                dividend_plot = plot_dividends_and_cagr(stock_data)
                if dividend_plot:
                    st.plotly_chart(dividend_plot, use_container_width=True)
        except Exception as e:
            st.error(f"An error occurred: {e}. Please check the ticker symbol and try again.")

    if st.session_state.initial_submit and st.session_state.stock_data is not None:
        min_date = st.session_state.stock_data['Date'].min()
        max_date = st.session_state.stock_data['Date'].max()

        start_date, end_date = st.slider(
            "Select date range",
            min_value=min_date.to_pydatetime(),
            max_value=max_date.to_pydatetime(),
            value=(st.session_state.start_date.to_pydatetime(), st.session_state.end_date.to_pydatetime()),
            format="YYYY-MM-DD"
        )

        submit_range_button = st.button('Submit Date Range')

        if submit_range_button:
            st.session_state.start_date = pd.to_datetime(start_date)
            st.session_state.end_date = pd.to_datetime(end_date)
            st.session_state.filtered_data = st.session_state.stock_data[(st.session_state.stock_data['Date'] >= st.session_state.start_date) & (st.session_state.stock_data['Date'] <= st.session_state.end_date)]

            st.session_state.filtered_data['Dividends'] = st.session_state.filtered_data['Dividends']
            a, b = annualized_return(st.session_state.filtered_data, 'Close')

            price_plot = plot_stock_data(st.session_state.filtered_data, a, b, ticker)
            drawdown_plot = plot_drawdown(st.session_state.filtered_data, ticker)

            st.plotly_chart(price_plot, use_container_width=True)
            st.plotly_chart(drawdown_plot, use_container_width=True)

            dividend_plot = plot_dividends_and_cagr(st.session_state.filtered_data)
            if dividend_plot:
                st.plotly_chart(dividend_plot, use_container_width=True)
