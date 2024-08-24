import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import streamlit as st

def app_stock_value():

    # Function to fetch and process data

    def fetch_data(ticker, discount_rate, inflation_rate, growth_model):
        stock = yf.Ticker(ticker)
        cash_flow = stock.cashflow

        try:
            # FCF 가져오기 (OCF = FCF + CapEx)
            fcf = cash_flow.loc['Free Cash Flow']
            capex = cash_flow.loc['Capital Expenditure']
        except KeyError as e:
            st.error(f"Error fetching data: {e}")
            return None

        ocf = fcf - capex

        # NaN 값 처리
        ocf = ocf.dropna()
        fcf = fcf.dropna()

        # 실제 연도 추출
        years_actual = ocf.index.year
        years_normalized = years_actual - years_actual.min()

        # OCF와 FCF 값을 배열로 변환
        ocf_values = np.array(ocf.values, dtype=float)
        fcf_values = np.array(fcf.values, dtype=float)

        # 복리 증가율 (r) 데이터 피팅
        def compound_growth(x, r, c):
            return c * (1 + r) ** x

        # 선형 증가율 (m) 데이터 피팅
        def linear_growth(x, m, b):
            return m * x + b

        initial_guess_ocf = [0.1, ocf_values[0]]
        initial_guess_fcf = [0.1, fcf_values[0]]

        if growth_model == 'Compound Growth':
            # Curve fitting for compound growth
            popt_ocf, _ = curve_fit(compound_growth, years_normalized, ocf_values, p0=initial_guess_ocf, maxfev=10000)
            popt_fcf, _ = curve_fit(compound_growth, years_normalized, fcf_values, p0=initial_guess_fcf, maxfev=10000)
            growth_func = compound_growth
            r_ocf = popt_ocf[0]
            c_ocf = popt_ocf[1]
            r_fcf = popt_fcf[0]
            c_fcf = popt_fcf[1]
        elif growth_model == 'Linear Growth':
            # Linear fitting for linear growth
            m_ocf, b_ocf = np.polyfit(years_normalized, ocf_values, 1)
            m_fcf, b_fcf = np.polyfit(years_normalized, fcf_values, 1)
            growth_func = linear_growth
            r_ocf = m_ocf
            c_ocf = b_ocf
            r_fcf = m_fcf
            c_fcf = b_fcf

        # 미래 데이터 계산
        n_years = 10
        all_years = np.arange(0, len(years_normalized) + n_years)
        future_years = np.arange(years_actual.max() + 1, years_actual.max() + n_years + 1)

        fitted_ocf = growth_func(all_years, r_ocf, c_ocf)
        fitted_fcf = growth_func(all_years, r_fcf, c_fcf)
        future_ocf = growth_func(np.arange(len(years_normalized), len(years_normalized) + n_years), r_ocf, c_ocf)
        future_fcf = growth_func(np.arange(len(years_normalized), len(years_normalized) + n_years), r_fcf, c_fcf)

        # 할인된 FCF 계산
        discounted_fcf = future_fcf / (1 + discount_rate) ** np.arange(1, n_years + 1)

        # CV (Continuing Value) 계산
        cv_values = future_ocf * (1 + inflation_rate) / (discount_rate - inflation_rate) / (1 + discount_rate) ** np.arange(1, n_years + 1)

        # Estimated Value 계산
        past_discounted_fcf_sum = np.sum(fcf_values / (1 + discount_rate) ** np.arange(1, len(fcf_values) + 1))
        estimated_value = past_discounted_fcf_sum + cv_values

        # yfinance에서 총 발행 주식 수 및 현재 주가 가져오기
        total_shares = stock.info['sharesOutstanding']
        current_price = stock.history(period='1d')['Close'].iloc[-1]

        # 데이터프레임 생성
        data = {
            'Year': np.concatenate([years_actual, future_years]),
            'OCF (Millions)': np.concatenate([ocf_values, future_ocf]) / 1e6,
            'FCF (Millions)': np.concatenate([fcf_values, future_fcf]) / 1e6,
            'Discounted FCF (Millions)': np.concatenate([np.full_like(fcf_values, np.nan), discounted_fcf]) / 1e6,
            'CV (Millions)': np.concatenate([np.full_like(fcf_values, np.nan), cv_values]) / 1e6,
            'Estimated Value (Millions)': np.concatenate([np.full_like(fcf_values, np.nan), estimated_value]) / 1e6,
            'Stock Price (USD)': np.concatenate([np.full_like(fcf_values, np.nan), estimated_value / total_shares])
        }

        df = pd.DataFrame(data)

        # Estimated stock price (10년 후) 계산
        estimated_stock_price = estimated_value[-1] / total_shares

        # 현재 주가와 비교
        percentage_difference = ((estimated_stock_price - current_price) / current_price) * 100

        return df, current_price, estimated_stock_price, percentage_difference, r_ocf, r_fcf

    # Streamlit UI
    st.title("Stock Value Estimation")

    # 주식 티커 입력
    ticker = st.text_input("주식 티커(ticker) 입력 (e.g., MSFT):", "MSFT")

    # 할인율 및 물가상승률 입력
    discount_rate = st.number_input("할인율 입력 (e.g., 10%):", value=10.0, min_value=0.0) / 100
    inflation_rate = st.number_input("물가상승률 입력 (e.g., 3%):", value=3.0, min_value=0.0) / 100

    # 성장 모델 선택 (Compound Growth vs. Linear Growth)
    growth_model = st.radio(
        "성장 모델 선택하기",
        ("Compound Growth", "Linear Growth")
    )

    if ticker:
        result = fetch_data(ticker, discount_rate, inflation_rate, growth_model)
        if result:
            df, current_price, estimated_stock_price, percentage_difference, r_ocf, r_fcf = result

            # Create tabs with Stock Price Comparison first
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["적정 주가 예상하기", "OCF Graph", "FCF Graph", "CV Graph", "데이터 테이블"])

            with tab1:
                st.subheader("Stock Price Comparison")

                # Display current stock price and estimated stock price
                st.write(f"**Current Stock Price:** ${current_price:.2f}")
                st.write(f"**Estimated Stock Price:** ${estimated_stock_price:.2f}")
                st.write("")

                # Calculate percentage difference
                if percentage_difference > 0:
                    st.markdown(f"<h4 style='color:red;'>**{ticker}의 주가는 {percentage_difference:.2f}% 저평가되었습니다.**</h3>", unsafe_allow_html=True)
                elif percentage_difference < 0:
                    st.markdown(f"<h4 style='color:red;'>**{ticker}의 주가는 {-percentage_difference:.2f}% 고평가되었습니다.**</h3>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h4 style='color:red;'>**{ticker}의 주가는 현재 적정가입니다.**</h3>", unsafe_allow_html=True)

                st.write("")
                st.write("✪ 지난 4년간의 OCF와 FCF의 복리 상승 추세를 기준으로 계산됩니다.")
                st.write("✪ 10년 동안 상승 추세를 지속한다고 가정합니다.")
                st.write("✪ 10년이후, 할인율의 성장 속도로 성장한다고 가정합니다.")

            # OCF 그래프 탭
            with tab2:
                st.subheader("OCF Graph")
                ocf_fig, ocf_ax = plt.subplots()
                ocf_ax.bar(df['Year'][:len(df['OCF (Millions)'][:len(df['OCF (Millions)']) - 10])], df['OCF (Millions)'][:len(df['OCF (Millions)']) - 10], label='Actual OCF', color='lightblue', alpha=0.6)
                ocf_ax.plot(df['Year'][-10:], df['OCF (Millions)'][-10:], label='Estimated OCF', color='blue', marker='o')
                ocf_ax.set_title(f"OCF for {ticker}")
                ocf_ax.set_xlabel("Year")
                ocf_ax.set_ylabel("OCF (in Millions)")
                ocf_ax.legend()
                ocf_ax.grid(True, linestyle = ":")
                st.pyplot(ocf_fig)
                st.write(f"**OCF Growth Rate:** {r_ocf*100:.2f}%")

            # FCF 그래프 탭
            with tab3:
                st.subheader("FCF Graph")
                fcf_fig, fcf_ax = plt.subplots()
                fcf_ax.bar(df['Year'][:len(df['FCF (Millions)'][:len(df['FCF (Millions)']) - 10])], df['FCF (Millions)'][:len(df['FCF (Millions)']) - 10], label='Actual FCF', color='salmon', alpha=0.6)
                fcf_ax.plot(df['Year'][-10:], df['FCF (Millions)'][-10:], label='Estimated FCF', color='red', marker='o')
                fcf_ax.set_title(f"FCF for {ticker}")
                fcf_ax.set_xlabel("Year")
                fcf_ax.set_ylabel("FCF (in Millions)")
                fcf_ax.legend()
                fcf_ax.grid(True, linestyle = ":")
                st.pyplot(fcf_fig)
                st.write(f"**FCF Growth Rate:** {r_fcf*100:.2f}%")

            # CV 그래프 탭
            with tab4:
                st.subheader("CV Graph")
                cv_fig, cv_ax = plt.subplots()
                cv_ax.plot(df['Year'][-10:], df['CV (Millions)'][-10:], label='Continuing Value Trend', color='green', marker='o')
                cv_ax.set_title(f"Continuing Value for {ticker}")
                cv_ax.set_xlabel("Year")
                cv_ax.set_ylabel("CV (in Millions)")
                cv_ax.legend()
                cv_ax.grid(True, linestyle = ":")
                st.pyplot(cv_fig)

            # Data Table 탭
            with tab5:
                st.subheader("Data Table")
                st.dataframe(df)
