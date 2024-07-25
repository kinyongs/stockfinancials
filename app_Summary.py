import streamlit as st
import requests
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

def app_Summary():

    st.title("Financial Dashboard")

    # Get Fear and Greed Index data
    @st.cache_data
    def get_fng_data():
        response = requests.get('https://api.alternative.me/fng/?limit=36500')
        fng_data = response.json()['data']
        fng_df = pd.DataFrame(fng_data)
        fng_df['timestamp'] = pd.to_datetime(fng_df['timestamp'], unit='s')
        fng_df.set_index('timestamp', inplace=True)
        fng_df['value'] = fng_df['value'].astype(int)
        return fng_df

    # Get S&P 500 stock data
    @st.cache_data
    def get_sp500_data(start_date, end_date):
        sp500_data = yf.download("^GSPC", start=start_date, end=end_date)
        return sp500_data

    # Calculate Drawdown
    def calculate_drawdown(df):
        cum_max = df['Close'].cummax()
        drawdown = (df['Close'] - cum_max) / cum_max
        return drawdown

    # Load data
    fng_df = get_fng_data()
    start_date = fng_df.index.min()
    end_date = fng_df.index.max()
    sp500_data = get_sp500_data(start_date, end_date)

    # Calculate drawdown
    sp500_data['Drawdown'] = calculate_drawdown(sp500_data)

    # Create interactive plots
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=sp500_data.index, y=sp500_data['Close'], mode='lines', name='S&P 500 Index'))

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sp500_data.index, y=sp500_data['Drawdown'], mode='lines', name='S&P 500 Drawdown'))

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=fng_df.index, y=fng_df['value'], mode='lines', name='Fear and Greed Index'))

    # Add ranges for Fear and Greed Index
    range_colors = {
        'Extreme Fear': ('rgba(255,0,0,0.2)', 0, 24),
        'Fear': ('rgba(255,165,0,0.2)', 25, 49),
        'Neutral': ('rgba(255,255,0,0.2)', 50, 74),
        'Greed': ('rgba(0,255,0,0.2)', 75, 89),
        'Extreme Greed': ('rgba(0,128,0,0.2)', 90, 100)
    }

    for label, (color, start, end) in range_colors.items():
        fig3.add_shape(
            type="rect",
            x0=fng_df.index.min(),
            x1=fng_df.index.max(),
            y0=start,
            y1=end,
            fillcolor=color,
            opacity=0.3,
            line=dict(color="rgba(0,0,0,0)")
        )

    # Update layout for S&P 500 and Drawdown charts
    for fig in [fig1, fig2]:
        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray', griddash='dot')

    # Update layout for Fear and Greed Index chart
    fig3.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray', griddash='dot')
    fig3.update_yaxes(
        showgrid=True, gridwidth=0.5, gridcolor='LightGray', griddash='dot',
        tickvals=[0, 24, 49, 74, 89, 100],
        
        ticktext=['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed', '']
    )
    fig3.update_layout(
        title='Fear and Greed Index',
        xaxis_title='Date',
        yaxis_title='Fear and Greed Index',
        yaxis=dict(range=[-10, 110])  # Adjust y-axis range to fit the indicators
    )

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["S&P 500", "Drawdown", "Fear and Greed Index", "Market News"])

    with tab1:
        st.subheader("S&P 500 Index")
        st.plotly_chart(fig1)

    with tab2:
        st.subheader("S&P 500 Drawdown")
        st.plotly_chart(fig2)

    with tab3:
        st.subheader("Fear and Greed Index")
        st.plotly_chart(fig3)

    with tab4:
        st.subheader("Market News")
        ticker = "SPY"  # S&P 500 ETF 티커
        stock = yf.Ticker(ticker)
        news = stock.news

        if news:
            news_df = pd.DataFrame(news)
            news_df['publish_time'] = news_df['providerPublishTime'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
            news_df = news_df[['title', 'link', 'publish_time']]
            news_df.columns = ['제목', '링크', '게시일']

            # 뉴스 데이터를 마크다운 형식으로 표시
            for index, row in news_df.iterrows():
                st.markdown(f"**[{row['제목']}]({row['링크']})**  \n게시일: {row['게시일']}")
        else:
            st.warning("해당 티커에 대한 뉴스를 찾을 수 없습니다.")
