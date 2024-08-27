import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from yahooquery import Ticker
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

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

    # 그래프 출력 함수 (주가 포함)
    def plot_1(item, key_name, color1, color2, ticker, stock_data):
        try:
            growth = item.pct_change() * 100
            growth = growth.infer_objects(copy=False)
        except Exception as e:
            print(f"Error processing growth calculation for {key_name}: {e}")
            growth = pd.Series([np.nan] * len(item), index=item.index)

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
                y=midpoint_y + (abs(item.iloc[i] - item.iloc[i-1]) * 0.4),  # 화살표의 중간 아래 위치
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
                title='Price',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            template='plotly_white',
            showlegend = False

        )

        return fig

    # 그래프 출력 함수 (주가 미포함)
    def plot_2(item, key_name, color1, color2):
        try:
            growth = item.pct_change() * 100
            growth = growth.infer_objects(copy=False)
        except Exception as e:
            print(f"Error processing growth calculation for {key_name}: {e}")
            growth = pd.Series([np.nan] * len(item), index=item.index)

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
                y=midpoint_y + (abs(item.iloc[i] - item.iloc[i-1]) * 0.4),  # 화살표의 중간 아래 위치
                text=f'{growth.iloc[i]:.1f}%',
                showarrow=False,
                font=dict(color=color2)
            )

        # 그래프 레이아웃 설정
        fig.update_layout(
            title=f'{key_name} 변화',
            xaxis_title='날짜',
            yaxis_title=key_name,
            legend_title=key_name,
            xaxis=dict(tickmode='array', tickvals=item.index, ticktext=item.index.strftime('%Y-%m-%d')),
            template='plotly_white',

        )

        return fig

    # Streamlit 앱 시작
    st.title("기업 재무 데이터")

    # 티커 입력과 기간 선택
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input("주식 티커를 입력하세요:")
    with col2:
        period = st.radio("기간을 선택하세요:", ("분기별", "연간"))

    if st.button("Show"):
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
                stock_data = yf.download(ticker, start=oldest_date, end=datetime.today().strftime('%Y-%m-%d'))
                stock_data['Close'] = stock_data['Close'].ffill()

                financials_df['주가'] = financials_df.index.to_series().apply(
                    lambda date: stock_data.loc[stock_data.index[stock_data.index.get_indexer([date], method='ffill')[0]], 'Close']
                )
                balance_sheet_df['주가'] = balance_sheet_df.index.to_series().apply(
                    lambda date: stock_data.loc[stock_data.index[stock_data.index.get_indexer([date], method='ffill')[0]], 'Close']
                )

                st.plotly_chart(plot_stock_price(stock_data, ticker, financials_df))


                
                try:
                    tabs1 = st.tabs(["매출", "영업이익", "영업 마진", "순이익"])

                    with tabs1[0]:
                        st.plotly_chart(plot_1(financials_df['Total Revenue'].dropna(), '매출', 'blue', 'red', ticker, stock_data))
                    with tabs1[1]:
                        st.plotly_chart(plot_1(financials_df['Operating Income'].dropna(), '영업 이익', 'green', 'red', ticker, stock_data))
                    with tabs1[2]:
                        st.plotly_chart(plot_2((financials_df['Operating Income'].dropna() / financials_df['Total Revenue']) * 100, '영업 마진', 'purple', 'red'))
                    with tabs1[3]:
                        st.plotly_chart(plot_1(financials_df['Net Income'].dropna(), '순이익', 'grey', 'red', ticker, stock_data))
                
                except KeyError:
                    st.error(f"관련 데이터가 없습니다.")

                try:
                    tabs2 = st.tabs(["자사주 매입", "배당금"])

                    with tabs2[0]:
                        st.plotly_chart(plot_2(-cashflow_df['Repurchase Of Capital Stock'].dropna(), '자사주 매입', 'brown', 'red'))
                    with tabs2[1]:
                        st.plotly_chart(plot_2(-cashflow_df['Cash Dividends Paid'].dropna(), '배당금', 'black', 'red'))
                except KeyError:
                    st.error(f"관련 데이터가 없습니다.")    
                
                try:
                    tabs3 = st.tabs(["CAPEX", "주식 수"])

                    with tabs3[0]:
                        st.plotly_chart(plot_2(-cashflow_df['Capital Expenditure'].dropna(), 'CAPEX', 'cyan', 'red'))
                    with tabs3[1]:
                        st.plotly_chart(plot_2(financials_df['Diluted Average Shares'].dropna(), '주식 수', 'magenta', 'red'))
                except KeyError:
                    st.error(f"관련 데이터가 없습니다.")

                try:    
                    tabs4 = st.tabs(["EPS", "DPS"])

                    with tabs4[0]:
                        st.plotly_chart(plot_1(financials_df['Diluted EPS'].dropna(), 'EPS', 'blue', 'red', ticker, stock_data))
                    with tabs4[1]:
                        st.plotly_chart(plot_1(-cashflow_df['Cash Dividends Paid'].dropna() / financials_df['Diluted Average Shares'], 'DPS', 'green', 'red', ticker, stock_data))
                except KeyError:
                    st.error(f"관련 데이터가 없습니다.")

                try:    
                    tabs5 = st.tabs(["PER", "PBR", "ROE"])

                    with tabs5[0]:
                        st.plotly_chart(plot_2(financials_df['주가'].dropna() / financials_df['Diluted EPS'].dropna(), 'PER', 'blue', 'red'))
                    with tabs5[1]:
                        st.plotly_chart(plot_2(balance_sheet_df['주가'].dropna() / (balance_sheet_df['Stockholders Equity'].dropna() / financials_df['Diluted Average Shares'].dropna()), 'PBR', 'green', 'red'))
                    with tabs5[2]:
                        st.plotly_chart(plot_2((financials_df['Net Income'] / balance_sheet_df['Stockholders Equity'].dropna()) * 100, 'ROE', 'orange', 'red'))
                except KeyError:
                    st.error(f"관련 데이터가 없습니다.")
                
                try:    
                    tabs6 = st.tabs(["Owner Earning", "목표 가격"])
                    with tabs6[0]:
                        st.plotly_chart(plot_1(financials_df['Net Income'].dropna() + cashflow_df['Depreciation And Amortization'].dropna() + cashflow_df['Capital Expenditure'].dropna(), 'Owner Earning', 'purple', 'red', ticker, stock_data))
                    with tabs6[1]:
                        financial_data = get_financial_data(ticker)
                        st.plotly_chart(plot_target_prices(financial_data, ticker))
                except KeyError:
                    st.error(f"관련 데이터가 없습니다.")
                