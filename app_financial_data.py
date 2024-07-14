import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from yahooquery import Ticker
import plotly.graph_objects as go

def app_financial_data():
    pd.set_option('future.no_silent_downcasting', True)

    # 배경 색깔 지정
    st.markdown(
        """
        <style>
        .reportview-container {background: white;}
        .main .block-container {background:white;}
        </style>
        """,
        unsafe_allow_html=True
    )

    # 금융 데이터 가져오기
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
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=stock_data.index, 
            y=stock_data['Close'], 
            mode='lines', 
            name='종가', 
            line=dict(color='darkblue')
        ))
        
        for date in financials_df.index:
            nearest_index = stock_data.index.get_indexer([date], method='nearest')[0]
            nearest_date = stock_data.index[nearest_index]
            fig.add_annotation(
                x=nearest_date, 
                y=stock_data.loc[nearest_date, 'Close'], 
                text='▼', 
                showarrow=True, 
                arrowhead=2, 
                arrowsize=1, 
                arrowwidth=2, 
                arrowcolor='red',
                ax=0, 
                ay=-10
            )

        fig.update_layout(
            title=f'{ticker} 주가 변화',
            xaxis_title='날짜',
            yaxis_title='주가',
            legend_title='범례',
            template='plotly_white'
        )

        return fig

    # 목표 가격 그래프 그리기
    def plot_target_prices(financial_data, ticker):
        target_labels = ['current', 'target-High', 'target-Low', 'target-Mean', 'target-Median']
        target_prices = [financial_data[label] for label in target_labels]
        
        fig = go.Figure()

        # 막대 그래프 그리기
        fig.add_trace(go.Bar(
            x=target_labels,
            y=target_prices,
            marker_color=['gray', 'royalblue', 'royalblue', 'royalblue', 'royalblue'],
            text=[f'{price:.2f}' for price in target_prices],
            textposition='auto',
            name='목표 가격'
        ))

        # 현재 가격을 y축에 표시
        current_price = financial_data['current']
        fig.add_hline(y=current_price, line_dash="dash", line_color="red", annotation_text=f'현재 가격: {current_price:.2f}')

        # 그래프 제목과 레이블 설정
        fig.update_layout(
            title=f'{ticker} 목표 가격',
            yaxis_title='가격',
            xaxis_title='',
            showlegend=False
        )

        return fig

    # 그래프 출력 함수
    def plot(item, key_name, color1, color2, ticker, stock_data):
        growth = item.pct_change() * 100
        growth = growth.infer_objects(copy=False)

        fig = go.Figure()

        # 막대 그래프 그리기
        fig.add_trace(go.Bar(
            x=item.index,
            y=item,
            marker_color=color1,
            name=key_name,
            text=[round(val, 2) for val in item],
            textposition='outside'
        ))

        # 변화율 화살표 및 텍스트 추가
        for i in range(1, len(item)):
            # 화살표 추가
            fig.add_annotation(
                x=item.index[i],
                y=item.iloc[i],
                ax=item.index[i-1],
                ay=item.iloc[i-1],
                xref='x',
                yref='y',
                axref='x',
                ayref='y',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor=color2
            )

            # 변화율 텍스트 추가 (화살표의 중간 아래에 위치)
            midpoint_x = item.index[i-1] + (item.index[i] - item.index[i-1]) / 2
            midpoint_y = (item.iloc[i] + item.iloc[i-1]) / 2
            fig.add_annotation(
                x=midpoint_x,
                y=midpoint_y - (abs(item.iloc[i] - item.iloc[i-1]) * 0.1),  # 화살표의 중간 아래 위치
                text=f'{growth.iloc[i]:.1f}%',
                showarrow=False,
                font=dict(color=color2)
            )

        # 보조 y축에 주가 추가
        fig.add_trace(go.Scatter(
            x=stock_data.index,
            y=stock_data['Close'],
            mode='lines',
            name='종가',
            yaxis='y2',
            line=dict(color='orange')
        ))

        # 그래프 레이아웃 설정
        fig.update_layout(
            title=f'{ticker} : {key_name} 변화',
            xaxis_title='날짜',
            yaxis_title=key_name,
            legend_title=key_name,
            xaxis=dict(tickmode='array', tickvals=item.index, ticktext=item.index.strftime('%Y-%m-%d')),
            yaxis2=dict(
                title='종가',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            template='plotly_white',
            legend=dict(
            x=0,
            y=0.2,
            xanchor='left',
            yanchor='top'
            )
        )

        return fig

    # Streamlit 앱 시작
    st.title("주식 분석기")

    # 티커 입력과 기간 선택
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input("주식 티커를 입력하세요:")
    with col2:
        period = st.radio("기간을 선택하세요:", ("분기별", "연간"))

    # 메트릭 선택
    st.subheader("표시할 메트릭 선택")
    cols = st.columns(4)
    metrics = {
        "매출": cols[0].checkbox('매출'),
        "영업 이익": cols[0].checkbox("영업 이익"),
        "영업 마진": cols[0].checkbox("영업 마진"),
        "순이익": cols[0].checkbox("순이익"),
        "CAPEX": cols[1].checkbox("CAPEX"),
        "자사주 매입": cols[1].checkbox('자사주 매입'),
        "배당금": cols[1].checkbox('배당금'),
        "주식 수": cols[1].checkbox('주식 수'),
        "EPS": cols[2].checkbox('EPS'),
        "DPS": cols[2].checkbox('DPS'),
        "PER": cols[2].checkbox('PER'),
        "PBR": cols[2].checkbox('PBR'),
        "ROE": cols[2].checkbox('ROE'),
        "Owner Earning": cols[3].checkbox('Owner Earning'),
        "목표 가격": cols[3].checkbox("목표 가격")
    }

    if st.button("그래프 생성"):
        if not ticker:
            st.warning("주식 티커를 입력하세요.")
        else:
            stock = yf.Ticker(ticker)

            try:
                if period == "분기별":
                    financials = stock.quarterly_financials
                    cashflow = stock.quarterly_cashflow
                    balance_sheet = stock.quarterly_balance_sheet
                else:
                    financials = stock.financials
                    cashflow = stock.cashflow
                    balance_sheet = stock.balance_sheet
            except Exception as e:
                st.error(f"금융 데이터를 가져오는데 실패했습니다: {e}")
                financials = pd.DataFrame()
                cashflow = pd.DataFrame()
                balance_sheet = pd.DataFrame()

            if financials.empty or cashflow.empty or balance_sheet.empty:
                st.error("금융 데이터를 가져오는데 실패했습니다. 티커 기호를 확인하세요.")
            else:
                financials_df = financials.T.sort_index()
                cashflow_df = cashflow.T.sort_index()
                balance_sheet_df = balance_sheet.T.sort_index()

                oldest_date = financials_df.index.min()
                stock_data = yf.download(ticker, start=oldest_date, end="2026-01-01")
                stock_data['Close'] = stock_data['Close'].ffill()

                financials_df['주가'] = financials_df.index.to_series().apply(
                    lambda date: stock_data.loc[stock_data.index[stock_data.index.get_indexer([date], method='ffill')[0]], 'Close']
                )
                balance_sheet_df['주가'] = balance_sheet_df.index.to_series().apply(
                    lambda date: stock_data.loc[stock_data.index[stock_data.index.get_indexer([date], method='ffill')[0]], 'Close']
                )

                st.plotly_chart(plot_stock_price(stock_data, ticker, financials_df))

                for key, val in metrics.items():
                    if val:
                        key_name = key
                        data_key = key.replace(" ", "_")
                        try:
                            if key_name == "매출":
                                data = financials_df['Total Revenue'] #/ 1e6
                            elif key_name == "영업 이익":
                                data = financials_df['Operating Income'] #/ 1e6
                            elif key_name == "영업 마진":
                                data = (financials_df['Operating Income'] / financials_df['Total Revenue']) * 100
                            elif key_name == "순이익":
                                data = financials_df['Net Income'] #/ 1e6
                            elif key_name == "CAPEX":
                                data = -cashflow_df['Capital Expenditure'] #/ 1e6
                            elif key_name == "자사주 매입":
                                data = -cashflow_df['Repurchase Of Capital Stock'] #/ 1e6
                            elif key_name == "배당금":
                                data = -(cashflow_df['Repurchase Of Capital Stock'] + cashflow_df['Cash Dividends Paid']) #/ 1e6
                            elif key_name == "주식 수":
                                data = financials_df['Diluted Average Shares'] #/ 1e6
                            elif key_name == "EPS":
                                data = financials_df['Diluted EPS']
                            elif key_name == "DPS":
                                data = -cashflow_df['Cash Dividends Paid'] / financials_df['Diluted Average Shares']
                            elif key_name == "PER":
                                data = financials_df['주가'] / financials_df['Diluted EPS']
                            elif key_name == "PBR":
                                data = balance_sheet_df['주가'] / (balance_sheet_df['Stockholders Equity'] / financials_df['Diluted Average Shares'])
                            elif key_name == "ROE":
                                data = (financials_df['Net Income'] / balance_sheet_df['Stockholders Equity']) * 100
                            elif key_name == "Owner Earning":
                                data = (financials_df['Net Income'] + cashflow_df['Depreciation And Amortization'] + cashflow_df['Capital Expenditure']) #/ 1e6
                            else:
                                continue
                            st.plotly_chart(plot(data.dropna(), key_name, 'gray', 'black', ticker, stock_data))
                        except KeyError:
                            st.error(f"{key_name}에 대한 데이터가 없습니다.")
                            continue

                if metrics["목표 가격"]:
                    financial_data = get_financial_data(ticker)
                    st.subheader("목표 가격")
                    target_prices_fig = plot_target_prices(financial_data, ticker)
                    st.plotly_chart(target_prices_fig)
