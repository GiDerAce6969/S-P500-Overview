import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="S&P 500 Simple Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

# --- Data Functions ---

def get_sp500_tickers():
    """
    Returns a list of S&P 500 tickers.
    In this simple version, the list is hardcoded for reliability.
    """
    # A smaller, representative list of S&P 500 companies
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'JPM', 'JNJ', 'V', 'PG',
        'UNH', 'HD', 'MA', 'BAC', 'DIS', 'PFE', 'XOM', 'CSCO', 'PEP', 'KO'
    ]

@st.cache_data(ttl=timedelta(hours=1)) # Cache data for 1 hour
def get_stock_data(ticker, start_date, end_date):
    """
    Downloads historical stock data from Yahoo Finance.
    """
    try:
        # Added auto_adjust=True to handle stock splits/dividends and silence the warning
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        if data.empty:
            st.warning(f"No data found for {ticker}. It might be a delisted stock or an error.")
            return pd.DataFrame()
        # Calculate some basic technical indicators
        data['Moving_Avg_50'] = data['Close'].rolling(window=50).mean()
        data['Daily_Return'] = data['Close'].pct_change()
        return data
    except Exception as e:
        st.error(f"Error downloading data for {ticker}: {e}")
        return pd.DataFrame()

# --- Main Application ---

st.title("Simple S&P 500 Stock Analyzer")
st.markdown("A demonstration of a simple stock analysis tool built with Streamlit and Yahoo Finance.")

# --- Sidebar for User Input ---
st.sidebar.header("Controls")

tickers = get_sp500_tickers()
selected_ticker = st.sidebar.selectbox("Select a Stock Ticker", tickers)

# Date range selection
end_date = datetime.today()
start_date = st.sidebar.date_input("Start Date", end_date - timedelta(days=365*5)) # Default to 5 years ago

# --- Data Loading and Display ---
if selected_ticker:
    st.header(f"Analyzing: {selected_ticker}")

    data = get_stock_data(selected_ticker, start_date, end_date)

    if not data.empty:
        # --- Key Metrics ---
        st.subheader("Key Metrics")
        latest_data = data.iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        
        # --- FIX IS HERE: Explicitly cast values to float/int before formatting ---
        col1.metric("Last Close Price", f"${float(latest_data['Close']):.2f}")
        col2.metric("50-Day Moving Avg", f"${float(latest_data['Moving_Avg_50']):.2f}")
        col3.metric("Latest Volume", f"{int(latest_data['Volume']):,}")
        col4.metric("Daily Return", f"{float(latest_data['Daily_Return']):.2%}")

        # --- Visualizations ---
        st.subheader("Price Chart")
        
        # Create the plot
        # Note: With auto_adjust=True, yfinance provides only 'Close' column, not OHL.
        # We will switch from Candlestick to a simple Line chart.
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'))
        
        fig.add_trace(go.Scatter(x=data.index, y=data['Moving_Avg_50'], 
                                 mode='lines', name='50-Day MA', line=dict(color='orange', width=1, dash='dot')))

        fig.update_layout(
            title=f'{selected_ticker} Stock Price',
            yaxis_title='Price (USD)',
            xaxis_title='Date',
            xaxis_rangeslider_visible=False # Hide the range slider
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Raw Data ---
        with st.expander("View Raw Data Table"):
            st.dataframe(data)

else:
    st.info("Please select a ticker from the sidebar to begin analysis.")
