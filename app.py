import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Superstore Sales & Profit Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- DATA LOADING AND PREPROCESSING ---
@st.cache_data
def load_data():
    """
    Load Superstore data from a URL and perform basic preprocessing.
    """
    # URL for the raw CSV data
    url = "https://raw.githubusercontent.com/dataprofessor/dashboard-v2/master/superstore.csv"
    df = pd.read_csv(url, encoding="ISO-8859-1")
    
    # Convert 'Order Date' to datetime objects
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d/%m/%Y')
    
    # Create a 'Month-Year' column for time series analysis
    df['Month-Year'] = df['Order Date'].dt.to_period('M').astype(str)
    
    return df

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Dashboard Filters")

# Region Filter
region = st.sidebar.multiselect(
    "Select Region:",
    options=df['Region'].unique(),
    default=df['Region'].unique()
)

# Category Filter
category = st.sidebar.multiselect(
    "Select Category:",
    options=df['Category'].unique(),
    default=df['Category'].unique()
)

# Segment Filter
segment = st.sidebar.multiselect(
    "Select Segment:",
    options=df['Segment'].unique(),
    default=df['Segment'].unique()
)

# Apply filters to the dataframe
df_filtered = df[
    df['Region'].isin(region) &
    df['Category'].isin(category) &
    df['Segment'].isin(segment)
]

# --- MAIN DASHBOARD ---
st.title("📊 Superstore Sales & Profitability Dashboard")
st.markdown("---")

# --- KEY PERFORMANCE INDICATORS (KPIs) ---
total_sales = int(df_filtered['Sales'].sum())
total_profit = int(df_filtered['Profit'].sum())
profit_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Total Sales")
    st.subheader(f"US $ {total_sales:,}")
with col2:
    st.subheader("Total Profit")
    st.subheader(f"US $ {total_profit:,}")
with col3:
    st.subheader("Profit Margin")
    st.subheader(f"{profit_margin:.2f}%")

st.markdown("---")

# --- VISUALIZATIONS ---

# 1. Monthly Sales and Profit Trend (Time-Series Analysis)
st.header("Monthly Sales & Profit Trend")
monthly_analysis = df_filtered.groupby('Month-Year').agg({'Sales':'sum', 'Profit':'sum'}).reset_index()

fig_monthly = px.line(
    monthly_analysis,
    x='Month-Year',
    y=['Sales', 'Profit'],
    title="Sales and Profit Over Time",
    labels={'value': 'Amount (USD)', 'variable': 'Metric'},
    color_discrete_map={"Sales": "#1f77b4", "Profit": "#2ca02c"}
)
fig_monthly.update_layout(xaxis={'type': 'category'}) # Treat x-axis as categorical
st.plotly_chart(fig_monthly, use_container_width=True)


# 2. Sales and Profit by Category and Sub-Category (Product Analysis)
col_cat, col_subcat = st.columns(2)

with col_cat:
    st.header("Sales by Product Category")
    sales_by_category = df_filtered.groupby('Category')['Sales'].sum().sort_values(ascending=False)
    fig_cat_sales = px.bar(
        sales_by_category,
        x=sales_by_category.values,
        y=sales_by_category.index,
        orientation='h',
        title="Total Sales by Category",
        labels={'x': 'Total Sales (USD)', 'y': 'Category'},
        text_auto='.2s'
    )
    st.plotly_chart(fig_cat_sales, use_container_width=True)

with col_subcat:
    st.header("Profit by Product Sub-Category")
    profit_by_subcat = df_filtered.groupby('Sub-Category')['Profit'].sum().sort_values(ascending=True)
    fig_subcat_profit = px.bar(
        profit_by_subcat,
        x=profit_by_subcat.values,
        y=profit_by_subcat.index,
        orientation='h',
        title="Total Profit by Sub-Category",
        labels={'x': 'Total Profit (USD)', 'y': 'Sub-Category'},
        text_auto='.2s'
    )
    # Color bars based on profit
    fig_subcat_profit.update_traces(marker_color=['#d62728' if x < 0 else '#2ca02c' for x in profit_by_subcat.values])
    st.plotly_chart(fig_subcat_profit, use_container_width=True)


# 3. Sales by Region and State (Geographical Analysis)
st.header("Geographical Performance")
sales_by_state = df_filtered.groupby('State')['Sales'].sum().reset_index()

fig_geo = px.choropleth(
    sales_by_state,
    locations='State',
    locationmode="USA-states",
    color='Sales',
    scope="usa",
    color_continuous_scale="Viridis",
    title="Total Sales by State"
)
st.plotly_chart(fig_geo, use_container_width=True)


# --- DATA TABLE ---
with st.expander("View Raw Data Table"):
    st.dataframe(df_filtered)
