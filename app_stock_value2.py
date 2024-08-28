import yfinance as yf
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def app_stock_value2():
    # Function to fetch and process data
    def fetch_stock_data(ticker):
        stock = yf.Ticker(ticker)
        financials_df = stock.financials
        balance_sheet_df = stock.balance_sheet

        # 현재 BPS와 현재 주가
        info = stock.info
        current_bps = info.get('bookValue', np.nan)
        current_price = stock.history(period='1d')['Close'].iloc[-1]

        try:
            # ROE 계산
            roe_series = financials_df.loc['Net Income'].dropna() / balance_sheet_df.loc['Stockholders Equity'].dropna()
            average_roe = roe_series.mean()

            if np.isnan(average_roe):
                raise ValueError("Could not retrieve sufficient data to calculate ROE.")

        except KeyError as e:
            st.error(f"Error fetching data: {e}")
            return None

        return current_bps, current_price, average_roe, roe_series

    # Function to calculate future stock price and percentage difference
    def calculate_future_price(current_bps, current_price, average_roe, N, target_return):
        # N년 후의 적정 주가 계산
        future_price = (current_bps * np.power(1 + average_roe, N)) / np.power(1 + target_return, N)
        
        # 현재 주가는 N년 후의 적정 주가 대비 몇 % 수준인가?
        percentage_of_future_price = (current_price / future_price) * 100
        
        return future_price, percentage_of_future_price

    # Function to generate a DataFrame of future prices by year
    def generate_yearly_future_prices(current_bps, average_roe, target_return, N):
        years = list(range(1, N + 1))
        future_prices = [(current_bps * np.power(1 + average_roe, year)) / np.power(1 + target_return, year) for year in years]
        return pd.DataFrame({"Year": years, "Estimated Future Price": future_prices})

    # Function to generate a DataFrame of future prices by varying target returns
    def generate_target_return_prices(current_bps, average_roe, N):
        target_returns = np.arange(0.01, 0.21, 0.01)  # 1% to 20%
        future_prices = [(current_bps * np.power(1 + average_roe, N)) / np.power(1 + r, N) for r in target_returns]
        return pd.DataFrame({"Target Return": target_returns, "Estimated Future Price": future_prices})

    # Streamlit UI
    st.title("ROE 기반 적정 주가 계산기")

    # 주식 티커 입력
    ticker = st.text_input("티커(ticker) 입력 (e.g., MSFT):", "MSFT")

    # N년 후와 목표 수익률 입력
    N = st.number_input("투자 기간 (N):", value=10, min_value=1)
    target_return = st.number_input("목표 수익률 (e.g., 10%):", value=10.0, min_value=0.0) / 100

    # Show 버튼 추가
    if st.button("Show Results"):
        if ticker:
            current_bps, current_price, average_roe, roe_series = fetch_stock_data(ticker)
            if current_bps is not None:
                # 미래 주가 계산
                future_price, percentage_of_future_price = calculate_future_price(current_bps, current_price, average_roe, N, target_return)

                # 연도별 적정 주가 계산
                future_price_df = generate_yearly_future_prices(current_bps, average_roe, target_return, N)

                # 목표 수익률에 따른 적정 주가 계산
                target_return_df = generate_target_return_prices(current_bps, average_roe, N)

                # Create tabs
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["결과", "ROE 시각화", "투자기간별 적정 주가", "기대수익률에 따른 적정 주가 변화", "수식"])

                with tab1:
                    st.subheader("Results")
                    st.write(f"**현재 주가:** ${current_price:.2f}")
                    st.write(f"**현재 BPS:** ${current_bps:.2f}")
                    st.write(f"**4년 평균 ROE:** {average_roe:.2%}")
                    st.write(f"**{N}년 후 적정 주가:** ${future_price:.2f}")
                    st.write(f"**현재 주가는 적정 주가 대비 {percentage_of_future_price:.2f}% 수준 입니다.**")
                    
                    if percentage_of_future_price < 100:
                        st.markdown(f"<h4 style='color:red;'>**{ticker} stock is undervalued by {-percentage_of_future_price + 100:.2f}%.**</h4>", unsafe_allow_html=True)
                    elif percentage_of_future_price > 100:
                        st.markdown(f"<h4 style='color:red;'>**{ticker} stock is overvalued by {percentage_of_future_price - 100:.2f}%.**</h4>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<h4 style='color:red;'>**{ticker} stock is currently at its fair value.**</h4>", unsafe_allow_html=True)

                with tab2:
                    st.subheader(f"ROE 데이터 시각화")
                    
                    # ROE 데이터를 시각화
                    fig, ax = plt.subplots()
                    roe_series.plot(kind='bar', ax=ax, color='skyblue')
                    ax.axhline(y=average_roe, color='red', linestyle='--', label=f'Avg. ROE: {average_roe:.2%}')
                    ax.set_xlabel("Period")
                    ax.set_ylabel("ROE")
                    ax.set_title(f"{ticker} ROE")
                    ax.legend()
                    st.pyplot(fig)
                
                
                with tab3:
                    st.subheader(f"Estimated Future Prices Over {N} Years")
                    
                    # Visualization of future prices by year
                    fig, ax = plt.subplots()
                    ax.plot(future_price_df['Year'], future_price_df['Estimated Future Price'], marker='o')
                    ax.set_xlabel("Year")
                    ax.set_ylabel("Estimated Future Price (USD)")
                    ax.set_title(f"Future Price of {ticker} Over {N} Years")
                    ax.grid(True, linestyle=':', linewidth=0.5)
                    st.pyplot(fig)

                with tab4:
                    st.subheader(f"Future Prices by Target Return for {N} Years")
                    
                    # Visualization of future prices by target return
                    fig, ax = plt.subplots()
                    ax.plot(target_return_df['Target Return'] * 100, target_return_df['Estimated Future Price'], marker='o')
                    ax.set_xlabel("Target Return (%)")
                    ax.set_ylabel("Estimated Future Price (USD)")
                    ax.set_title(f"Impact of Target Return on Future Price of {ticker}")
                    ax.grid(True, linestyle=':', linewidth=0.5)
                    st.pyplot(fig)

                with tab5:
                    st.subheader("계산 공식")

                    st.latex(r'''
                    \text{미래 주가} = \frac{\text{현재 BPS} \times (1 + \text{평균 ROE})^N}{(1 + \text{목표 수익률})^N}
                    ''')
                    
                    st.write("**해당 수식에서:**")
                    st.write("- **현재 BPS**: 현재 주당순자산가치")
                    st.write("- **평균 ROE**: 평균 자기자본이익률")
                    st.write("- **목표 수익률**: 목표하는 수익률")
                    st.write("- **N**: 투자 기간(년)")

                with tab5:
                    st.subheader(f"ROE 데이터 시각화")
                    
                    # ROE 데이터를 시각화
                    fig, ax = plt.subplots()
                    roe_series.plot(kind='bar', ax=ax, color='skyblue')
                    ax.axhline(y=average_roe, color='red', linestyle='--', label=f'Avg. ROE: {average_roe:.2%}')
                    ax.set_xlabel("Period")
                    ax.set_ylabel("ROE")
                    ax.set_title(f"{ticker} ROE")
                    ax.legend()
                    st.pyplot(fig)
