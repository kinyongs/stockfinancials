import streamlit as st
import requests
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import fear_and_greed

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
    # 현재 Fear and Greed Index 값 및 날짜 가져오기
    index_object = fear_and_greed.get()
    current_value = float(index_object.value)  # 'value' 속성을 사용하여 현재 값 가져오기
    fetch_date = datetime.now().strftime('%Y-%m-%d')  # 현재 날짜 가져오기

    # 레이블 및 범위 정의
    labels = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
    ranges = [0, 25, 45, 55, 75, 100]

    # 색상 정의 (50% 투명도)
    colors_with_alpha = ['rgba(255, 179, 179, 0.5)',  # Extreme Fear
                         'rgba(255, 217, 179, 0.5)',  # Fear
                         'rgba(255, 255, 179, 0.5)',  # Neutral
                         'rgba(217, 255, 179, 0.5)',  # Greed
                         'rgba(179, 255, 179, 0.5)']  # Extreme Greed

    # 색상으로 구분된 사각형 추가
    for i, (start, end) in enumerate(zip(ranges[:-1], ranges[1:])):
        fig3.add_shape(
            type="rect",
            x0=start,
            x1=end,
            y0=0,
            y1=1,
            line=dict(color="black", width=1),
            fillcolor=colors_with_alpha[i]  # 색상 적용
        )

    # 현재 값을 나타내는 빨간 점 추가
    fig3.add_trace(go.Scatter(
        x=[current_value],
        y=[0.5],
        mode='markers+text',
        text=[f'{current_value:.2f}'],
        textposition='bottom center',
        marker=dict(color='red', size=12)
    ))

    # 그래프 레이아웃 설정
    fig3.update_layout(
        title=f'Fear and Greed Index (as of {fetch_date})',
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            range=[0, 100],
            title='',
            zeroline=False,
            showline=False
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            range=[-0.5, 1],
            title='',
            zeroline=False,
            showline=False
        ),
        height=200,
        margin=dict(l=0, r=0, t=40, b=20),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # 레이블 추가
    for i, label in enumerate(labels):
        position = (ranges[i] + ranges[i + 1]) / 2
        fig3.add_annotation(
            x=position,
            y=-0.1,
            text=label,
            showarrow=False,
            font=dict(size=12),
            xanchor='center'
        )



    # Update layout for S&P 500 and Drawdown charts
    for fig in [fig1, fig2]:
        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray', griddash='dot')



    # Create tabs
    # tab1, tab2, tab3, tab4 = st.tabs(["S&P 500", "Drawdown", "Fear and Greed Index", "Market News"])
    tab1, tab2, tab3, tab4 = st.tabs(["S&P 500", "Drawdown", "Fear and Greed Index"])

    with tab1:
        st.subheader("S&P 500 Index")
        st.plotly_chart(fig1)

    with tab2:
        st.subheader("S&P 500 Drawdown")
        st.plotly_chart(fig2)

    with tab3:
        st.subheader("Crypto Fear and Greed Index")
            # Streamlit에 그래프 표시
        st.plotly_chart(fig3)

    # with tab4:
    #     st.subheader("Market News")
    #     ticker = "SPY"  # S&P 500 ETF 티커
    #     stock = yf.Ticker(ticker)
    #     news = stock.news

    #     if news:
    #         news_df = pd.DataFrame(news)
    #         news_df['publish_time'] = news_df['providerPublishTime'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
    #         news_df = news_df[['title', 'link', 'publish_time']]
    #         news_df.columns = ['제목', '링크', '게시일']

    #         # 뉴스 데이터를 마크다운 형식으로 표시
    #         for index, row in news_df.iterrows():
    #             st.markdown(f"**[{row['제목']}]({row['링크']})**  \n게시일: {row['게시일']}")
    #     else:
    #         st.warning("해당 티커에 대한 뉴스를 찾을 수 없습니다.")
