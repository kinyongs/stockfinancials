import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd
from scipy.optimize import curve_fit
import plotly.graph_objects as go
from datetime import datetime

def app_sp500():
    # FRED API 키 설정
    fred = Fred(api_key='209bb86d622d41883054b17d644e13b9')

    # 초기 날짜 설정
    start_date = '1900-01-01'
    end_date = '2030-12-31'

    # 데이터 가져오기 함수
    def fetch_data():
        sp500 = yf.download('^GSPC', start=start_date, end=end_date)
        m2 = fred.get_series('M2SL', start_date=start_date, end_date=end_date)
        gdp = fred.get_series('GDP', start_date=start_date, end_date=end_date)
        recession = fred.get_series('USREC', start_date=start_date, end_date=end_date)
        cpi = fred.get_series('CPIAUCSL', start_date=start_date, end_date=end_date)
        ten_year_treasury = fred.get_series('GS10', start_date=start_date, end_date=end_date)
        unemployment_rate = fred.get_series('UNRATE', start_date=start_date, end_date=end_date)
        return sp500, m2, gdp, recession, cpi, ten_year_treasury, unemployment_rate

    # EPS 데이터 가져오기 함수
    def fetch_eps_data(file_path):
        eps_data = pd.read_csv(file_path, parse_dates=['Date'])
        eps_data.set_index('Date', inplace=True)
        return eps_data

    # 데이터 전처리 함수
    def preprocess_data(sp500, m2, gdp, recession, eps_data, cpi, ten_year_treasury, unemployment_rate):
        sp500.index = pd.to_datetime(sp500.index)
        m2.index = pd.to_datetime(m2.index)
        gdp.index = pd.to_datetime(gdp.index)
        recession.index = pd.to_datetime(recession.index)
        cpi.index = pd.to_datetime(cpi.index)
        ten_year_treasury.index = pd.to_datetime(ten_year_treasury.index)
        unemployment_rate.index = pd.to_datetime(unemployment_rate.index)

        data = pd.DataFrame(index=sp500.index)
        data['S&P 500'] = sp500['Adj Close']
        data = data.join(m2.rename('M2'), how='left')
        data = data.join(gdp.rename('GDP'), how='left')
        data = data.join(recession.rename('Recession'), how='left')
        data = data.join(eps_data.rename(columns={'sp500EPS': 'EPS'}), how='left')
        data = data.join(cpi.rename('CPI'), how='left')
        data = data.join(ten_year_treasury.rename('Ten Year Treasury'), how='left')
        data = data.join(unemployment_rate.rename('Unemployment Rate'), how='left')
        data.ffill(inplace=True)

        return data

    # 경기 침체 기간 계산 함수
    def calculate_recession_periods(data):
        recession_ranges = []
        is_in_recession = False
        for date, value in data['Recession'].items():
            if value == 1 and not is_in_recession:
                start_date = date
                is_in_recession = True
            elif value == 0 and is_in_recession:
                end_date = date
                recession_ranges.append((start_date, end_date))
                is_in_recession = False
        return recession_ranges

    # Drawdown 계산 함수
    def calculate_drawdown(sp500):
        sp500['Peak'] = sp500['Adj Close'].cummax()
        sp500['Drawdown'] = (sp500['Adj Close'] - sp500['Peak']) / sp500['Peak']
        return sp500

    # CAGR 함수 정의
    def cagr(t, a, b):
        return a * (1 + b)**(t / 365.25)

    # 주가 데이터 피팅 함수
    def fit_data(sp500):
        sp500['Days'] = (sp500.index - sp500.index[0]).days
        popt, _ = curve_fit(cagr, sp500['Days'], sp500['Adj Close'], p0=(sp500['Adj Close'].iloc[0], 0.1))
        return popt

    # 연간 수익률 계산 함수
    def calculate_annual_returns(data):
        annual_data = data.resample('Y').last()
        annual_data = annual_data.drop(columns=['M2', 'Recession', 'EPS', 'Ten Year Treasury', 'Unemployment Rate'])
        annual_returns = annual_data.pct_change().dropna()
        
        return annual_returns

    # 그래프 생성 함수
    def plot_sp500_price_and_fitting(data, recession_ranges, sp500, popt, cagr_percent, log_scale):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=sp500.index, y=sp500['Adj Close'], mode='lines', name='S&P 500'))
        fig.add_trace(go.Scatter(x=sp500.index, y=cagr(sp500['Days'], *popt), mode='lines', name=f'Fitting (CAGR: {cagr_percent:.2%})'))

        for start, end in recession_ranges:
            fig.add_vrect(x0=start, x1=end, fillcolor="lightgray", opacity=0.5, line_width=0)

        if log_scale:
            fig.update_yaxes(type="log")

        fig.update_layout(title='S&P 500 Index and Fitting', xaxis_title='Date', yaxis_title='S&P 500 Index', legend=dict(x=0, y=1,xanchor='left', yanchor='top'))
        st.plotly_chart(fig)

    def plot_drawdown(data, recession_ranges, sp500):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=sp500.index, y=sp500['Drawdown'], fill='tozeroy', mode='none', name='Drawdown'))

        for start, end in recession_ranges:
            fig.add_vrect(x0=start, x1=end, fillcolor="lightgray", opacity=0.5, line_width=0)

        fig.update_layout(title='S&P 500 Drawdown', xaxis_title='Date', yaxis_title='Drawdown', legend=dict(x=0, y=1,xanchor='left', yanchor='top'))
        st.plotly_chart(fig)

    def plot_sp500_and_eps(data, recession_ranges, sp500, log_scale):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=data.index, y=data['S&P 500'], mode='lines', name='S&P 500'))
        fig.add_trace(go.Scatter(x=data.index, y=data['EPS'], mode='lines', name='EPS', yaxis='y2'))

        for start, end in recession_ranges:
            fig.add_vrect(x0=start, x1=end, fillcolor="lightgray", opacity=0.5, line_width=0)

        if log_scale:
            fig.update_yaxes(type="log")

        fig.update_layout(
            title='S&P 500 and EPS with Recession Periods',
            xaxis_title='Date',
            yaxis=dict(title='S&P 500', side='left'),
            yaxis2=dict(title='EPS', side='right', overlaying='y'),
            legend=dict(x=0, y=1,xanchor='left', yanchor='top')
        )
        st.plotly_chart(fig)

    def plot_sp500_and_m2(data, recession_ranges, sp500, log_scale):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=data.index, y=data['S&P 500'], mode='lines', name='S&P 500'))
        fig.add_trace(go.Scatter(x=data.index, y=data['M2'], mode='lines', name='M2', yaxis='y2'))

        for start, end in recession_ranges:
            fig.add_vrect(x0=start, x1=end, fillcolor="lightgray", opacity=0.5, line_width=0)

        if log_scale:
            fig.update_yaxes(type="log")

        fig.update_layout(
            title='S&P 500 and M2 with Recession Periods',
            xaxis_title='Date',
            yaxis=dict(title='S&P 500', side='left'),
            yaxis2=dict(title='M2 (Millions of $)', side='right', overlaying='y'),
            legend=dict(x=0, y=1,xanchor='left', yanchor='top')

        )
        st.plotly_chart(fig)

    def plot_sp500_and_gdp(data, recession_ranges, sp500, log_scale):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=data.index, y=data['S&P 500'], mode='lines', name='S&P 500'))
        fig.add_trace(go.Scatter(x=data.index, y=data['GDP'], mode='lines', name='GDP', yaxis='y2'))

        for start, end in recession_ranges:
            fig.add_vrect(x0=start, x1=end, fillcolor="lightgray", opacity=0.5, line_width=0)

        if log_scale:
            fig.update_yaxes(type="log")

        fig.update_layout(
            title='S&P 500 and GDP with Recession Periods',
            xaxis_title='Date',
            yaxis=dict(title='S&P 500', side='left'),
            yaxis2=dict(title='GDP (Millions of $)', side='right', overlaying='y'),
            legend=dict(x=0, y=1,xanchor='left', yanchor='top')
        )
        st.plotly_chart(fig)

    def plot_sp500_and_ten_year_treasury(data, recession_ranges, sp500, log_scale):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=data.index, y=data['S&P 500'], mode='lines', name='S&P 500'))
        fig.add_trace(go.Scatter(x=data.index, y=data['Ten Year Treasury'], mode='lines', name='Ten Year Treasury', yaxis='y2'))

        for start, end in recession_ranges:
            fig.add_vrect(x0=start, x1=end, fillcolor="lightgray", opacity=0.5, line_width=0)

        if log_scale:
            fig.update_yaxes(type="log")

        fig.update_layout(
            title='S&P 500 and 10-Year Treasury Yield with Recession Periods',
            xaxis_title='Date',
            yaxis=dict(title='S&P 500', side='left'),
            yaxis2=dict(title='10-Year Treasury Yield (%)', side='right', overlaying='y'),
            legend=dict(x=0, y=1,xanchor='left', yanchor='top')
        )
        st.plotly_chart(fig)

    def plot_sp500_and_unemployment_rate(data, recession_ranges, sp500, log_scale):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=data.index, y=data['S&P 500'], mode='lines', name='S&P 500'))
        fig.add_trace(go.Scatter(x=data.index, y=data['Unemployment Rate'], mode='lines', name='Unemployment Rate', yaxis='y2'))

        for start, end in recession_ranges:
            fig.add_vrect(x0=start, x1=end, fillcolor="lightgray", opacity=0.5, line_width=0)

        if log_scale:
            fig.update_yaxes(type="log")

        fig.update_layout(
            title='S&P 500 and Unemployment Rate with Recession Periods',
            xaxis_title='Date',
            yaxis=dict(title='S&P 500', side='left'),
            yaxis2=dict(title='Unemployment Rate (%)', side='right', overlaying='y'),
            legend=dict(x=0, y=1,xanchor='left', yanchor='top')
        )
        st.plotly_chart(fig)

    # def plot_annual_returns(data):
    #     fig = go.Figure()

    #     annual_returns = calculate_annual_returns(data)
    #     fig.add_trace(go.Bar(x=annual_returns.index.strftime('%Y'), y=annual_returns['S&P 500'], name='S&P 500'))

    #     fig.update_layout(title='S&P 500 Annual Returns', xaxis_title='Year', yaxis_title='Annual Return', legend=dict(x=0, y=1,xanchor='left', yanchor='top'))
    #     st.plotly_chart(fig)

    def plot_annual_returns(data):
        fig = go.Figure()

        annual_returns = calculate_annual_returns(data)
        annual_returns_percent = annual_returns['S&P 500'] * 100  # 백분율로 변환
        colors = ['green' if val >= 0 else 'red' for val in annual_returns_percent]
        
        fig.add_trace(go.Bar(
            x=annual_returns.index.strftime('%Y'),
            y=annual_returns_percent,
            name='S&P 500',
            marker_color=colors,
            text=[f'{val:.2f}%' for val in annual_returns_percent],  # 백분율 라벨 추가
            textposition='outside'
        ))

        fig.update_layout(
            title='S&P 500 Annual Returns',
            xaxis_title='Year',
            yaxis_title='Annual Return (%)',
            legend=dict(x=0, y=1, xanchor='left', yanchor='top')
        )
        st.plotly_chart(fig)



    # Streamlit 애플리케이션
    def main():
        st.title('S&P 500 index and Macro data')

        sp500, m2, gdp, recession, cpi, ten_year_treasury, unemployment_rate = fetch_data()
        eps_data = fetch_eps_data('data/sp500EPS.csv')
        data = preprocess_data(sp500, m2, gdp, recession, eps_data, cpi, ten_year_treasury, unemployment_rate)
        recession_ranges = calculate_recession_periods(data)
        sp500 = calculate_drawdown(sp500)

        # st.header('Overview')

        st.subheader('S&P 500 Price and Fitting')
        st.markdown('This plot shows the S&P 500 adjusted close price over time with an exponential fit.')
        log_scale_price_fitting = st.checkbox('Log Scale Price Fitting', value=False, key='log_scale_price_fitting')
        popt = fit_data(sp500)
        cagr_percent = popt[1]
        plot_sp500_price_and_fitting(data, recession_ranges, sp500, popt, cagr_percent, log_scale_price_fitting)

        st.subheader('S&P 500 Drawdown')
        st.markdown('This plot shows the drawdown of the S&P 500 over time.')
        plot_drawdown(data, recession_ranges, sp500)

        st.subheader('S&P 500 Annual Returns')
        st.markdown('This plot shows the annual returns of the S&P 500.')
        plot_annual_returns(data)

        st.subheader('S&P 500 and EPS')
        st.markdown('This plot shows the S&P 500 adjusted close price and EPS over time.')
        log_scale_eps = st.checkbox('Log Scale EPS', value=False, key='log_scale_eps')
        plot_sp500_and_eps(data, recession_ranges, sp500, log_scale_eps)

        st.subheader('S&P 500 and M2')
        st.markdown('This plot shows the S&P 500 adjusted close price and M2 money supply over time.')
        log_scale_m2 = st.checkbox('Log Scale M2', value=False, key='log_scale_m2')
        plot_sp500_and_m2(data, recession_ranges, sp500, log_scale_m2)

        st.subheader('S&P 500 and GDP')
        st.markdown('This plot shows the S&P 500 adjusted close price and GDP over time.')
        log_scale_gdp = st.checkbox('Log Scale GDP', value=False, key='log_scale_gdp')
        plot_sp500_and_gdp(data, recession_ranges, sp500, log_scale_gdp)

        st.subheader('S&P 500 and 10-Year Treasury Yield')
        st.markdown('This plot shows the S&P 500 adjusted close price and 10-Year Treasury Yield over time.')
        log_scale_treasury = st.checkbox('Log Scale Treasury Yield', value=False, key='log_scale_treasury')
        plot_sp500_and_ten_year_treasury(data, recession_ranges, sp500, log_scale_treasury)

        st.subheader('S&P 500 and Unemployment Rate')
        st.markdown('This plot shows the S&P 500 adjusted close price and Unemployment Rate over time.')
        log_scale_unemployment = st.checkbox('Log Scale Unemployment Rate', value=False, key='log_scale_unemployment')
        plot_sp500_and_unemployment_rate(data, recession_ranges, sp500, log_scale_unemployment)

    # if __name__ == '__main__':
    main()
