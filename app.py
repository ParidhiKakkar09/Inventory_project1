import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Intelligent Inventory Optimization",
    page_icon="📦",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv('data/cleaned_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

st.title("📦 Intelligent Inventory Optimization System")
st.markdown("---")

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.title("🔧 Filters")

# 1. Category Filter
category = st.sidebar.multiselect(
    "Select Category",
    options=df['category'].unique(),
    default=df['category'].unique()
)

# 2. Region Filter
region = st.sidebar.multiselect(
    "Select Region",
    options=df['region'].unique(),
    default=df['region'].unique()
)

# 3. Store Filter (NEW)
store = st.sidebar.multiselect(
    "Select Store",
    options=sorted(df['store_id'].unique()),
    default=sorted(df['store_id'].unique())
)

# 4. Date Range Slider (NEW)
st.sidebar.markdown("### 📅 Date Range")
min_date = df['date'].min().date()
max_date = df['date'].max().date()
start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Apply all filters
filtered_df = df[
    (df['category'].isin(category)) &
    (df['region'].isin(region)) &
    (df['store_id'].isin(store)) &
    (df['date'] >= pd.Timestamp(start_date)) &
    (df['date'] <= pd.Timestamp(end_date))
]

# ============================================================
# KPI CARDS
# ============================================================
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Products", filtered_df['product_id'].nunique())
with col2:
    st.metric("Low Stock Items", filtered_df[filtered_df['reorder_alert'] == 'Yes'].shape[0])
with col3:
    st.metric("Total Units Sold", f"{filtered_df['units_sold'].sum():,}")
with col4:
    st.metric("Avg Forecast Error", round((filtered_df['demand_forecast'] - filtered_df['units_sold']).mean(), 2))

st.markdown("---")

# ============================================================
# CHARTS ROW 1
# ============================================================
col1, col2 = st.columns(2)
with col1:
    st.subheader("Sales by Category")
    cat_sales = filtered_df.groupby('category')['units_sold'].sum().reset_index()
    fig1 = px.bar(cat_sales, x='category', y='units_sold', color='category')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Sales by Region")
    reg_sales = filtered_df.groupby('region')['units_sold'].sum().reset_index()
    fig2 = px.pie(reg_sales, values='units_sold', names='region')
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# CHARTS ROW 2
# ============================================================
col3, col4 = st.columns(2)
with col3:
    st.subheader("Sales by Season")
    season_sales = filtered_df.groupby('seasonality')['units_sold'].sum().reset_index()
    fig3 = px.bar(season_sales, x='seasonality', y='units_sold', color='seasonality')
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Forecast Accuracy by Category")
    forecast_acc = filtered_df.groupby('category').agg(
        avg_forecast=('demand_forecast', 'mean'),
        avg_actual=('units_sold', 'mean')
    ).reset_index()
    fig4 = px.bar(forecast_acc, x='category', y=['avg_forecast', 'avg_actual'], barmode='group')
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ============================================================
# DEMAND FORECAST CHART
# ============================================================
st.subheader("Demand Forecast vs Actual Sales")
monthly = filtered_df.groupby('date').agg(
    actual_sales=('units_sold', 'sum'),
    forecast=('demand_forecast', 'sum')
).reset_index()
monthly['moving_avg'] = monthly['actual_sales'].rolling(3).mean()
fig5 = px.line(monthly, x='date', y=['actual_sales', 'forecast', 'moving_avg'],
               title='Demand Forecast vs Actual Sales')
st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

# ============================================================
# WHAT-IF SCENARIO (NEW)
# ============================================================
st.subheader("🔮 What-If Scenario — Discount Impact on Sales")
st.markdown("Move the slider to see how changing discount affects predicted sales")

discount_val = st.slider(
    "Set Discount Percentage (%)",
    min_value=0,
    max_value=50,
    value=10,
    step=1
)

avg_sales_per_discount = filtered_df.groupby('discount')['units_sold'].mean().reset_index()
baseline_sales = filtered_df['units_sold'].mean()
discount_effect = baseline_sales * (1 + (discount_val - filtered_df['discount'].mean()) / 100)

col1, col2 = st.columns(2)
with col1:
    st.metric(
        "Predicted Avg Units Sold at Selected Discount",
        f"{discount_effect:,.0f} units"
    )
with col2:
    st.metric(
        "Baseline Avg Units Sold",
        f"{baseline_sales:,.0f} units"
    )

fig6 = px.bar(
    avg_sales_per_discount,
    x='discount', y='units_sold',
    title='Average Sales at Each Discount Level',
    labels={'discount': 'Discount %', 'units_sold': 'Avg Units Sold'}
)
fig6.add_vline(x=discount_val, line_dash="dash", line_color="red",
               annotation_text=f"Selected: {discount_val}%")
st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ============================================================
# LIVE REORDER RECOMMENDATIONS (NEW)
# ============================================================
st.subheader("🚨 Live Reorder Recommendations")
st.markdown("Products that need to be reordered RIGHT NOW based on current stock levels")

reorder_df = filtered_df[filtered_df['reorder_alert'] == 'Yes'].groupby(
    ['store_id', 'product_id', 'category']
).agg(
    avg_inventory=('inventory_level', 'mean'),
    avg_daily_sales=('units_sold', 'mean'),
    avg_units_ordered=('units_ordered', 'mean')
).reset_index()

reorder_df['days_until_stockout'] = (
    reorder_df['avg_inventory'] / reorder_df['avg_daily_sales']
).round(1)

reorder_df['recommended_order_qty'] = (
    reorder_df['avg_daily_sales'] * 30
).round(0).astype(int)

reorder_df = reorder_df.sort_values('days_until_stockout').head(20)
reorder_df.columns = ['Store', 'Product', 'Category',
                       'Avg Inventory', 'Avg Daily Sales',
                       'Avg Units Ordered', 'Days Until Stockout',
                       'Recommended Order Qty']

st.dataframe(reorder_df, use_container_width=True)

st.markdown("---")

# ============================================================
# CSV DOWNLOAD BUTTON (NEW)
# ============================================================
st.subheader("📥 Download Filtered Data")

csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Download Current Filtered Data as CSV",
    data=csv,
    file_name='filtered_inventory_data.csv',
    mime='text/csv'
)