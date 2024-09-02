import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

def app_stock_DCA() :

    # Streamlit 앱 시작
    st.title("실제 주가 기반의 적립식 투자 분석")

    # 현재 연도 계산
    current_year = datetime.now().year

    # 사용자 입력
    ticker = st.text_input("주식 티커를 입력하세요 (예: MSFT):", value="MSFT")
    start_year = st.number_input("투자 시작 연도:", min_value=1900, max_value=current_year, value=2010)
    investment_period = st.number_input("투자 기간 (년):", min_value=1, max_value=100, value=10)
    monthly_investment = st.number_input("월간 투자 금액 ($):", min_value=1, value=100)
    reinvest_dividends = st.radio("배당금 재투자 여부:", ('예', '아니오')) == '예'
    show_results = st.button("Show")

    # 투자 시작 연도와 투자 기간 검증
    if start_year + investment_period > current_year:
        st.error(f"투자 시작 연도와 투자 기간의 합이 현재 연도({current_year})를 초과할 수 없습니다.")
    else:
        # yfinance 데이터를 이용해 주가 정보 가져오기
        stock_data = yf.download(ticker, start=f"{start_year-1}-01-01", end=f"{start_year + investment_period}-12-31")
        stock_data.reset_index(inplace=True)

        # 주가 데이터가 비어 있는지 확인하고 경고 메시지 출력
        if stock_data.empty:
            st.warning("해당 주식에 대한 데이터를 가져올 수 없습니다. 입력한 티커가 올바른지 확인하세요.")
        elif stock_data['Date'].dt.year.min() > start_year:
            earliest_date = stock_data['Date'].dt.date.min()
            st.warning(f"투자 시작 연도에 해당하는 데이터가 없습니다. 가장 이른 주식 데이터는 {earliest_date}에 시작됩니다.")
        else:
            # 적립식 투자(DCA) 계산 함수
            def calculate_dca(stock_data, start_year, investment_period, monthly_investment, reinvest_dividends):
                dates = stock_data['Date']
                close_prices = stock_data['Close']
                adj_close_prices = stock_data['Adj Close']

                start_date_index = dates[dates.dt.year == start_year].index[0]
                end_date_index = dates[dates.dt.year == start_year + investment_period].index[-1]

                investment_values, portfolio_values, total_dividends, shares_held, investment_dates = [], [], [], [], []

                total_investment = 0
                total_shares = 0
                total_dividends_received = 0
                current_month = dates[start_date_index].month

                for i in range(start_date_index, end_date_index + 1):
                    date = dates[i]
                    if date.month != current_month:
                        total_investment += monthly_investment
                        shares_bought = monthly_investment / close_prices[i]
                        total_shares += shares_bought
                        current_month = date.month

                    # 배당금 계산: 현재 보유 주식에 대한 실제 배당금
                    dividend_per_share = close_prices[i-1] - (adj_close_prices[i-1] / adj_close_prices[i]) * close_prices[i]
                    dividend = total_shares * dividend_per_share * 0.85
                    total_dividends_received += dividend

                    if reinvest_dividends and dividend > 0.1:
                        shares_bought_with_dividends = dividend / close_prices[i]
                        total_shares += shares_bought_with_dividends

                    investment_values.append(total_investment)
                    portfolio_values.append(total_shares * close_prices[i])
                    total_dividends.append(total_dividends_received)
                    shares_held.append(total_shares)
                    investment_dates.append(date)

                return pd.DataFrame({
                    "날짜": investment_dates,
                    "투자 금액": investment_values,
                    "포트폴리오 가치": portfolio_values,
                    "수익 가치": [pv - iv for pv, iv in zip(portfolio_values, investment_values)],
                    "배당금": total_dividends,
                    "보유 주식 수": shares_held
                })

            # 결과 보기 버튼 클릭 시 실행
            if show_results:
                # DCA 계산 수행
                results = calculate_dca(stock_data, start_year, investment_period, monthly_investment, reinvest_dividends)

                # 탭 생성
                tab1, tab2, tab3, tab4 = st.tabs(["투자금 및 자산", "배당금 변화", "보유 주식 수", "월별 투자 성과"])

                with tab1:
                    st.subheader("투자금 및 자산 가치 ($)")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=results["날짜"], y=results["투자 금액"], name="투자 금액"))
                    fig.add_trace(go.Bar(x=results["날짜"], y=results["수익 가치"], name="자산 가치"))
                    fig.update_layout(barmode='stack', legend=dict(x=0, y=1, traceorder="normal", bgcolor="rgba(0,0,0,0)"))
                    st.plotly_chart(fig)

                with tab2:
                    st.subheader("시간에 따른 배당금 변화 ($)")
                    fig = go.Figure([go.Bar(x=results["날짜"], y=results["배당금"], name="배당금")])
                    st.plotly_chart(fig)

                with tab3:
                    st.subheader("시간에 따른 보유 주식 수")
                    fig = go.Figure([go.Bar(x=results["날짜"], y=results["보유 주식 수"], name="보유 주식 수")])
                    st.plotly_chart(fig)

                with tab4:
                    st.subheader("월별 투자 성과")
                    # 날짜를 년월로 변환하여 그룹화
                    results['년월'] = results['날짜'].dt.to_period('M')
                    monthly_results = results.groupby('년월').last().reset_index()

                    # 월별 투자 성과를 테이블로 표시
                    st.table(monthly_results[["년월", "투자 금액", "포트폴리오 가치", "보유 주식 수"]])
