import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from yahooquery import Ticker

# Target Price 가져오기
def get_financial_data(ticker_symbol):
    ticker = Ticker(ticker_symbol)
    financial_data = ticker.financial_data[ticker_symbol]
    
    data = {
        'current': financial_data.get('currentPrice', 'N/A'),
        'target-High': financial_data.get('targetHighPrice', 'N/A'),
        'target-Low': financial_data.get('targetLowPrice', 'N/A'),
        'target-Mean': financial_data.get('targetMeanPrice', 'N/A'),
        'target-Median': financial_data.get('targetMedianPrice', 'N/A')
    }
    
    return data

# 주가 변화 그래프 그리기
def plot_stock_price(stock_data, ticker, financials_df):
    fig, ax = plt.subplots()
    
    stock_data['Close'].plot(ax=ax, color='darkblue', label='Close Price')
    
    for date in financials_df.index:
        nearest_index = stock_data.index.get_indexer([date], method='nearest')[0]
        nearest_date = stock_data.index[nearest_index]
        ax.annotate('▼', xy=(nearest_date, stock_data.loc[nearest_date, 'Close']), xytext=(nearest_date, stock_data.loc[nearest_date, 'Close'] + 10),
                    arrowprops=dict(color='red', arrowstyle='->'), color='red', ha='center')
    
    ax.set_title(f'{ticker} Stock Price Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Stock Price')
    ax.legend()
    plt.grid(True, linestyle=":")

    return fig

# Target Prices 그래프 그리기 함수
def plot_target_prices(financial_data, ticker):
    fig, ax = plt.subplots()
    target_labels = ['current', 'target-High', 'target-Low', 'target-Mean', 'target-Median']
    target_prices = [financial_data[label] for label in target_labels]
    
    # 막대 그래프 그리기
    bars = ax.bar(target_labels, target_prices, color=['gray', 'royalblue', 'royalblue', 'royalblue', 'royalblue'])

    # 각 막대 위에 가격 표시
    for bar, price in zip(bars, target_prices):
        ax.text(bar.get_x() + bar.get_width()/2.0, bar.get_height(), f'{price:.2f}', ha='center', va='bottom')

    # current 값을 y축 전체에 표시
    current_price = financial_data['current']
    ax.axhline(y=current_price, color='red', linestyle='--', label=f'Current Price: {current_price:.2f}')

    # 그래프 제목과 레이블 설정
    ax.set_title(f'{ticker} Target Prices')
    ax.set_ylabel('Price')
    ax.legend()
    plt.grid(True, linestyle=":")

    return fig

# 그래프 출력 함수
def plot(item, key_name, color1, color2, ticker):
    growth = item.pct_change() * 100

    fig, ax = plt.subplots()
    width = 0.4

    x = range(len(item))

    bars1 = ax.bar([p for p in x], item, width=width, label=key_name, color=color1)

    for bar in bars1:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval, round(yval, 2), va='bottom', color=color1)

    for i in range(1, len(item)):
        ax.annotate('', xy=(i - 1, item.iloc[i - 1]), xytext=(i, item.iloc[i]),
                    arrowprops=dict(arrowstyle='<-', color=color2, linestyle=":"))
        ax.text(i - 0.5, (item.iloc[i - 1] + item.iloc[i]) / 2, f'{growth.iloc[i]:.1f}%', color=color2, ha='center')

    ax.set_xticks([p for p in x])
    ax.set_xticklabels(item.index.strftime('%Y-%m-%d'), rotation=45)
    ax.set_xlabel('Date')
    ax.set_ylabel(key_name)
    ax.set_title(f'{ticker} : {key_name} over Time')
    ax.legend(loc='lower right')
    plt.grid(True, linestyle=":")
    plt.tight_layout()

    return fig

# Streamlit 앱 시작
st.title("Stock Analyzer")

# Ticker 입력과 기간 선택
col1, col2 = st.columns([2, 1])
with col1:
    ticker = st.text_input("Enter Stock Ticker:")
with col2:
    period = st.radio("Select Period:", ("Quarterly", "Annually"))

# 메트릭 선택
st.subheader("Select Metrics to Display")
cols = st.columns(4)
metrics = {
    "Revenue": cols[0].checkbox('Revenue'),
    "Operating Income": cols[0].checkbox("Operating Income"),
    "Operating Margin": cols[0].checkbox("Operating Margin"),
    "Net Income": cols[0].checkbox("Net Income"),
    "CAPEX": cols[1].checkbox("CAPEX"),
    "Buyback": cols[1].checkbox('Buyback'),
    "Dividend": cols[1].checkbox('Dividend'),
    "Number of Shares": cols[1].checkbox('Number of Shares'),
    "EPS": cols[2].checkbox('EPS'),
    "DPS": cols[2].checkbox('DPS'),
    "PER": cols[2].checkbox('PER'),
    "PBR": cols[2].checkbox('PBR'),
    "ROE": cols[2].checkbox('ROE'),
    "Owner Earning": cols[3].checkbox('Owner Earning'),
    "Target Prices": cols[3].checkbox("Target Prices")
}

if st.button("Generate Plots"):
    if not ticker:
        st.warning("Please enter a stock ticker.")
    else:
        stock = yf.Ticker(ticker)

        try:
            if period == "Quarterly":
                financials = stock.quarterly_financials
                cashflow = stock.quarterly_cashflow
                balance_sheet = stock.quarterly_balance_sheet
            else:
                financials = stock.financials
                cashflow = stock.cashflow
                balance_sheet = stock.balance_sheet
        except Exception as e:
            st.error(f"Failed to retrieve financial data: {e}")
            financials = pd.DataFrame()
            cashflow = pd.DataFrame()
            balance_sheet = pd.DataFrame()

        if financials.empty or cashflow.empty or balance_sheet.empty:
            st.error("Failed to retrieve financial data. Please check the ticker symbol.")
        else:
            financials_df = financials.T.sort_index()
            cashflow_df = cashflow.T.sort_index()
            balance_sheet_df = balance_sheet.T.sort_index()

            oldest_date = financials_df.index.min()
            stock_data = yf.download(ticker, start=oldest_date, end="2026-01-01")
            stock_data['Close'] = stock_data['Close'].ffill()

            financials_df['Stock Price'] = financials_df.index.to_series().apply(
                lambda date: stock_data.loc[stock_data.index[stock_data.index.get_indexer([date], method='ffill')[0]], 'Close']
            )
            balance_sheet_df['Stock Price'] = balance_sheet_df.index.to_series().apply(
                lambda date: stock_data.loc[stock_data.index[stock_data.index.get_indexer([date], method='ffill')[0]], 'Close']
            )

            st.pyplot(plot_stock_price(stock_data, ticker, financials_df))

            for key, val in metrics.items():
                if val:
                    key_name = key
                    data_key = key.replace(" ", "_")
                    try:
                        if key_name == "Revenue":
                            data = financials_df['Total Revenue'] / 1e6
                        elif key_name == "Operating Income":
                            data = financials_df['Operating Income'] / 1e6
                        elif key_name == "Operating Margin":
                            data = (financials_df['Operating Income'] / financials_df['Total Revenue']) * 100
                        elif key_name == "Net Income":
                            data = financials_df['Net Income'] / 1e6
                        elif key_name == "CAPEX":
                            data = -cashflow_df['Capital Expenditure'] / 1e6
                        elif key_name == "Buyback":
                            data = -cashflow_df['Repurchase Of Capital Stock'] / 1e6
                        elif key_name == "Dividend":
                            data = -(cashflow_df['Repurchase Of Capital Stock'] + cashflow_df['Cash Dividends Paid']) / 1e6
                        elif key_name == "Number of Shares":
                            data = financials_df['Diluted Average Shares'] / 1e6
                        elif key_name == "EPS":
                            data = financials_df['Diluted EPS']
                        elif key_name == "DPS":
                            data = -cashflow_df['Cash Dividends Paid'] / financials_df['Diluted Average Shares']
                        elif key_name == "PER":
                            data = financials_df['Stock Price'] / financials_df['Diluted EPS']
                        elif key_name == "PBR":
                            data = balance_sheet_df['Stock Price'] / (balance_sheet_df['Stockholders Equity'] / financials_df['Diluted Average Shares'])
                        elif key_name == "ROE":
                            data = (financials_df['Net Income'] / balance_sheet_df['Stockholders Equity']) * 100
                        elif key_name == "Owner Earning":
                            data = (financials_df['Net Income'] + cashflow_df['Depreciation And Amortization'] + cashflow_df['Capital Expenditure']) / 1e6
                        else:
                            continue
                        st.pyplot(plot(data.dropna(), key_name, 'gray', 'black', ticker))
                    except KeyError:
                        st.error(f"Data for {key_name} not available.")
                        continue

            if metrics["Target Prices"]:
                financial_data = get_financial_data(ticker)
                st.subheader("Target Prices")
                st.pyplot(plot_target_prices(financial_data, ticker))
