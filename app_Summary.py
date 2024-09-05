import streamlit as st
import requests
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import fear_and_greed
import matplotlib.pyplot as plt

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

    # Get S&P 500 stock data for the last 5 years
    @st.cache_data
    def get_sp500_data_5years(start_date, end_date):
        sp500_data = yf.download("^GSPC", start=start_date, end=end_date)
        return sp500_data

    # Get S&P 500 stock data for the entire available date range (for seasonality)
    @st.cache_data
    def get_sp500_data_full():
        sp500_data = yf.download("^GSPC", period="max")  # Get the maximum available data
        return sp500_data

    # Calculate Drawdown
    def calculate_drawdown(df):
        cum_max = df['Close'].cummax()
        drawdown = (df['Close'] - cum_max) / cum_max
        return drawdown

    # Load Fear and Greed Index data
    fng_df = get_fng_data()

    # Get the date range for the last 5 years
    start_date = fng_df.index.min()
    end_date = fng_df.index.max()

    # Load the last 5 years of S&P 500 data
    sp500_data_5years = get_sp500_data_5years(start_date, end_date)

    # Load full range S&P 500 data for seasonality
    sp500_data_full = get_sp500_data_full()

    # Calculate drawdown for the last 5 years of data
    sp500_data_5years['Drawdown'] = calculate_drawdown(sp500_data_5years)

    # Create interactive plots for S&P 500 (last 5 years) and Drawdown
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=sp500_data_5years.index, y=sp500_data_5years['Close'], mode='lines', name='S&P 500 Index (5 years)'))

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sp500_data_5years.index, y=sp500_data_5years['Drawdown'], mode='lines', name='S&P 500 Drawdown (5 years)'))

    fig3 = go.Figure()
    index_object = fear_and_greed.get()
    current_value = float(index_object.value)
    fetch_date = datetime.now().strftime('%Y-%m-%d')

    labels = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
    ranges = [0, 25, 45, 55, 75, 100]
    colors_with_alpha = ['rgba(255, 179, 179, 0.5)', 'rgba(255, 217, 179, 0.5)', 'rgba(255, 255, 179, 0.5)', 'rgba(217, 255, 179, 0.5)', 'rgba(179, 255, 179, 0.5)']

    for i, (start, end) in enumerate(zip(ranges[:-1], ranges[1:])):
        fig3.add_shape(type="rect", x0=start, x1=end, y0=0, y1=1, line=dict(color="black", width=1), fillcolor=colors_with_alpha[i])

    fig3.add_trace(go.Scatter(x=[current_value], y=[0.5], mode='markers+text', text=[f'{current_value:.2f}'], textposition='bottom center', marker=dict(color='darkred', size=12)))

    fig3.update_layout(title=f'Fear and Greed Index (as of {fetch_date})', xaxis=dict(showgrid=False, showticklabels=False, range=[0, 100], title='', zeroline=False, showline=False), yaxis=dict(showgrid=False, showticklabels=False, range=[-0.5, 1], title='', zeroline=False, showline=False), height=200, margin=dict(l=0, r=0, t=40, b=20), plot_bgcolor='white', paper_bgcolor='white')

    for i, label in enumerate(labels):
        position = (ranges[i] + ranges[i + 1]) / 2
        fig3.add_annotation(x=position, y=-0.1, text=label, showarrow=False, font=dict(size=12), xanchor='center')

    # Update layout for S&P 500 and Drawdown charts
    for fig in [fig1, fig2]:
        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray', griddash='dot')
        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGray', griddash='dot')

    # Function to plot seasonality with additional options (using full range data)
    @st.cache_data
    def plot_seasonality(sp500_data, selected_year=None):
        sp500_data['Return'] = sp500_data['Adj Close'].pct_change()
        sp500_data = sp500_data.dropna(subset=['Return'])

        sp500_data['Year'] = sp500_data.index.year
        sp500_data['DayOfYear'] = sp500_data.index.dayofyear

        # Calculate geometric mean return by DayOfYear
        sp500_data['GeometricReturn'] = 1 + sp500_data['Return']
        geometric_mean_return = sp500_data.groupby('DayOfYear')['GeometricReturn'].prod() ** (1 / sp500_data['Year'].nunique()) - 1
        cumulative_geometric_return = (1 + geometric_mean_return).cumprod() - 1

        # Plot seasonality
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(cumulative_geometric_return.index, cumulative_geometric_return.values * 100, label='S&P 500 (Seasonality)', linewidth=2, color='royalblue')

        # Set up second y-axis
        if selected_year:
            ax2 = ax1.twinx()  # Create a second y-axis sharing the same x-axis
            selected_year_data = sp500_data[sp500_data['Year'] == selected_year].groupby('DayOfYear')['GeometricReturn'].prod().cumprod() - 1
            ax2.plot(selected_year_data.index, selected_year_data.values * 100, label=f'{selected_year}', linewidth=2, color='red')

            # Set second y-axis label
            ax2.set_ylabel(f'{selected_year} Cumulative Geometric Return (%)', color='darkred')
            ax2.tick_params(axis='y', labelcolor='darkred')

        # Set up labels and ticks for first y-axis
        months = pd.date_range(start='2023-01-01', periods=12, freq='M').strftime('%b')
        month_days = [pd.Timestamp(f'2023-{month:02d}-01').day_of_year for month in range(1, 13)]
        ax1.set_xticks(month_days)
        ax1.set_xticklabels(months)

        ax1.set_xlim(1, 365)
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Cumulative Geometric Return (%)')
        ax1.set_title('Cumulative Geometric Return by Month (Seasonality)')
        ax1.grid(True)
        ax1.legend(loc='upper left')

        if selected_year:
            ax2.legend(loc='upper right')

        st.pyplot(fig)


    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["S&P 500", "Drawdown", "Fear and Greed Index", "Seasonality"])

    with tab1:
        st.subheader("S&P 500 Index (Last 5 Years)")
        st.plotly_chart(fig1)

    with tab2:
        st.subheader("S&P 500 Drawdown (Last 5 Years)")
        st.plotly_chart(fig2)

    with tab3:
        st.subheader("Crypto Fear and Greed Index")
        st.plotly_chart(fig3)

    with tab4:
        st.subheader("S&P 500 Seasonality")

        # Input box for user to select a year
        selected_year = st.text_input('Enter a year to plot (e.g., 2020)', '2024')

        # Show button
        if st.button('Show'):
            if selected_year.isdigit():
                plot_seasonality(sp500_data_full, int(selected_year))
            else:
                st.warning('Please enter a valid year.')
        else:
            plot_seasonality(sp500_data_full)  # Default plot with the recent year
