import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Dynamic Sales & Profit Dashboard",
    page_icon="💼",
    layout="wide"
)

# --- DATA LOADING AND PROCESSING FUNCTIONS ---
@st.cache_data
def load_data(uploaded_file):
    """
    Load data from an uploaded file (CSV or Excel) and perform preprocessing.
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None

        # --- DATA CLEANING AND PREPARATION ---
        # Standardize column names (e.g., convert to lowercase and replace spaces)
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')

        # Find the correct date column (handles variations like 'order_date' or 'Order Date')
        date_col = next((col for col in df.columns if 'order_date' in col), None)
        if not date_col:
            st.error("Could not find an 'Order Date' column in the uploaded file.")
            return None
            
        # Convert 'Order Date' to datetime objects with robust parsing
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df.dropna(subset=[date_col], inplace=True) # Drop rows where date conversion failed

        # Create 'Month-Year' for time series analysis
        df['month_year'] = df[date_col].dt.to_period('M').astype(str)

        return df

    except Exception as e:
        st.error(f"Error processing the file: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("Dashboard Controls")
    st.write("Use the sample data or upload your own file to analyze.")
    
    data_source = st.radio(
        "Choose a data source:",
        ("Use Sample Superstore Data", "Upload Your Own File")
    )
    
    uploaded_file = None
    if data_source == "Upload Your Own File":
        uploaded_file = st.file_uploader(
            "Upload your CSV or Excel file",
            type=['csv', 'xls', 'xlsx']
        )
        st.info(
            """
            **Note:** Your file must contain columns like 'Order Date', 
            'Sales', 'Profit', 'Region', 'Category', and 'Segment'.
            """
        )

# --- LOAD DATA BASED ON USER CHOICE ---
if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    # Load the default sample data if no file is uploaded
    # The function is decorated with @st.cache_data, so this is efficient
    @st.cache_data
    def load_sample_data():
        return load_data(open("data/superstore.csv", "rb"))
    df = load_sample_data()


# --- MAIN DASHBOARD (RUNS ONLY IF DATA IS LOADED SUCCESSFULLY) ---
if df is not None and not df.empty:
    # Rename columns for consistency, assuming they exist after standardization
    df.rename(columns={'region': 'Region', 'category': 'Category', 'segment': 'Segment', 
                       'sales': 'Sales', 'profit': 'Profit', 'sub_category': 'Sub-Category',
                       'state': 'State', 'month_year': 'Month-Year'}, inplace=True, errors='ignore')

    # --- Sidebar Filters (Dynamically created from the loaded data) ---
    st.sidebar.header("Dashboard Filters")
    region = st.sidebar.multiselect("Select Region:", options=df['Region'].unique(), default=df['Region'].unique())
    category = st.sidebar.multiselect("Select Category:", options=df['Category'].unique(), default=df['Category'].unique())
    segment = st.sidebar.multiselect("Select Segment:", options=df['Segment'].unique(), default=df['Segment'].unique())

    # Apply filters
    df_filtered = df[
        df['Region'].isin(region) &
        df['Category'].isin(category) &
        df['Segment'].isin(segment)
    ]

    # --- MAIN DASHBOARD LAYOUT ---
    st.title("📊 Dynamic Sales & Profitability Dashboard")
    st.markdown("---")

    # KPIs
    total_sales = int(df_filtered['Sales'].sum())
    total_profit = int(df_filtered['Profit'].sum())
    profit_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Sales", f"US $ {total_sales:,}")
    with col2: st.metric("Total Profit", f"US $ {total_profit:,}")
    with col3: st.metric("Profit Margin", f"{profit_margin:.2f}%")

    st.markdown("---")

    # VISUALIZATIONS
    st.header("Monthly Sales & Profit Trend")
    monthly_analysis = df_filtered.groupby('Month-Year').agg({'Sales':'sum', 'Profit':'sum'}).reset_index()
    fig_monthly = px.line(monthly_analysis, x='Month-Year', y=['Sales', 'Profit'], title="Sales and Profit Over Time")
    fig_monthly.update_layout(xaxis={'type': 'category'})
    st.plotly_chart(fig_monthly, use_container_width=True)

    col_cat, col_subcat = st.columns(2)
    with col_cat:
        st.header("Sales by Category")
        sales_by_category = df_filtered.groupby('Category')['Sales'].sum().sort_values(ascending=False)
        fig_cat_sales = px.bar(sales_by_category, orientation='h', text_auto='.2s')
        st.plotly_chart(fig_cat_sales, use_container_width=True)

    with col_subcat:
        st.header("Profit by Sub-Category")
        profit_by_subcat = df_filtered.groupby('Sub-Category')['Profit'].sum().sort_values(ascending=True)
        fig_subcat_profit = px.bar(profit_by_subcat, orientation='h', text_auto='.2s')
        fig_subcat_profit.update_traces(marker_color=['#d62728' if x < 0 else '#2ca02c' for x in profit_by_subcat.values])
        st.plotly_chart(fig_subcat_profit, use_container_width=True)

    st.header("Geographical Performance")
    sales_by_state = df_filtered.groupby('State')['Sales'].sum().reset_index()
    fig_geo = px.choropleth(sales_by_state, locations='State', locationmode="USA-states", color='Sales', scope="usa")
    st.plotly_chart(fig_geo, use_container_width=True)

    with st.expander("View Raw Data Table"):
        st.dataframe(df_filtered)

else:
    # This message shows when the app starts and is waiting for a file, or if a file fails to load
    st.title("📊 Dynamic Sales & Profitability Dashboard")
    st.info("Please upload a file or use the sample data to begin analysis.")
