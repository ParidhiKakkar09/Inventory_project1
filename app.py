import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Intelligent Inventory Optimization",
    page_icon="📦",
    layout="wide"
)

@st.cache_data
def load_default_data():
    df = pd.read_csv('data/cleaned_data.csv')
    df['date'] = pd.to_datetime(df['date'], format='mixed')
    return df

# ============================================================
# CSV UPLOAD SECTION
# ============================================================
st.title("📦 Intelligent Inventory Optimization System")
st.markdown("---")

st.subheader("📂 Upload New Inventory Data (Optional)")
st.markdown("Upload a new CSV file to update the entire dashboard automatically. If no file is uploaded, the default dataset is used.")

uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df['date'] = pd.to_datetime(df['date'], format='mixed')
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')
    if 'reorder_alert' not in df.columns:
        df['reorder_alert'] = df['inventory_level'].apply(lambda x: 'Yes' if x < 100 else 'No')
    st.success(f"✅ New data uploaded successfully! {len(df):,} rows loaded.")
else:
    df = load_default_data()
    st.info("ℹ️ Using default dataset — 73,100 rows loaded.")

st.markdown("---")

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.title("🔧 Filters")

category = st.sidebar.multiselect(
    "Select Category",
    options=df['category'].unique(),
    default=df['category'].unique()
)

region = st.sidebar.multiselect(
    "Select Region",
    options=df['region'].unique(),
    default=df['region'].unique()
)

store = st.sidebar.multiselect(
    "Select Store",
    options=sorted(df['store_id'].unique()),
    default=sorted(df['store_id'].unique())
)

st.sidebar.markdown("### 📅 Date Range")
min_date = df['date'].min().date()
max_date = df['date'].max().date()
start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

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
# WHAT-IF SCENARIO
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
# PHASE 4 — COST OPTIMIZATION (NEW)
# ============================================================
st.subheader("💰 Cost Optimization Analysis")
st.markdown("Identifies which products are costing the most money due to overstock or understock")

cost_df = filtered_df.groupby(['store_id', 'product_id', 'category']).agg(
    avg_inventory=('inventory_level', 'mean'),
    avg_units_sold=('units_sold', 'mean'),
    avg_price=('price', 'mean')
).reset_index()

# Holding cost = 2% of price per unit sitting in stock
cost_df['holding_cost'] = (cost_df['avg_inventory'] * cost_df['avg_price'] * 0.02).round(2)

# Stockout cost = difference between sold and inventory × 10% penalty
cost_df['stockout_cost'] = (
    (cost_df['avg_units_sold'] - cost_df['avg_inventory']).clip(lower=0) *
    cost_df['avg_price'] * 0.10
).round(2)

# Total cost
cost_df['total_cost'] = (cost_df['holding_cost'] + cost_df['stockout_cost']).round(2)

# Recommendation
cost_df['recommendation'] = cost_df.apply(
    lambda row: '🔴 Reduce Stock — Overstock' if row['holding_cost'] > row['stockout_cost']
    else '🟡 Increase Stock — Understock', axis=1
)

cost_df = cost_df.sort_values('total_cost', ascending=False).head(20)
cost_df.columns = ['Store', 'Product', 'Category', 'Avg Inventory',
                    'Avg Units Sold', 'Avg Price', 'Holding Cost (₹)',
                    'Stockout Cost (₹)', 'Total Cost (₹)', 'Recommendation']

st.dataframe(cost_df, use_container_width=True)

# Cost chart
cost_chart = cost_df.head(10)
fig7 = px.bar(
    cost_chart,
    x='Category',
    y=['Holding Cost (₹)', 'Stockout Cost (₹)'],
    barmode='group',
    title='Top 10 Products by Inventory Cost',
    color_discrete_map={
        'Holding Cost (₹)': '#EF553B',
        'Stockout Cost (₹)': '#636EFA'
    }
)
st.plotly_chart(fig7, use_container_width=True)
st.info("ℹ️ Stockout Cost is near zero across all products — indicating an overstock situation in this retail store. Focus should be on reducing holding costs by optimizing order quantities.")

st.markdown("---")

# ============================================================
# PHASE 4 — REORDER OPTIMIZATION (NEW)
# ============================================================
st.subheader("📦 Reorder Optimization")
st.markdown("Tells you exactly WHEN to reorder and HOW MUCH to order with priority levels")

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

# Priority levels
reorder_df['priority'] = reorder_df['days_until_stockout'].apply(
    lambda x: '🔴 Critical — Order Today' if x <= 1
    else ('🟡 Warning — Order This Week' if x <= 3
    else '🟢 OK — Monitor')
)

reorder_df = reorder_df.sort_values('days_until_stockout')
reorder_df.columns = ['Store', 'Product', 'Category',
                       'Avg Inventory', 'Avg Daily Sales',
                       'Avg Units Ordered', 'Days Until Stockout',
                       'Recommended Order Qty', 'Priority']

st.dataframe(reorder_df.head(20), use_container_width=True)

st.markdown("---")

# ============================================================
# PHASE 4 — DEMAND BASED STOCK OPTIMIZATION (NEW)
# ============================================================
st.subheader("📊 Demand Based Stock Optimization")
st.markdown("Recommends ideal stock levels per category per season to avoid overstock and understock")

season_opt = filtered_df.groupby(['category', 'seasonality']).agg(
    avg_demand=('demand_forecast', 'mean'),
    avg_actual_sales=('units_sold', 'mean'),
    avg_current_stock=('inventory_level', 'mean')
).reset_index()

# Optimal stock = average demand × 1.2 (20% safety buffer)
season_opt['optimal_stock'] = (season_opt['avg_demand'] * 1.2).round(0)

# Stock status
season_opt['stock_status'] = season_opt.apply(
    lambda row: '🔴 Overstock — Reduce Order' if row['avg_current_stock'] > row['optimal_stock'] * 1.3
    else ('🟡 Understock — Increase Order' if row['avg_current_stock'] < row['optimal_stock'] * 0.7
    else '🟢 Optimal Stock Level'), axis=1
)

season_opt.columns = ['Category', 'Season', 'Avg Demand',
                       'Avg Actual Sales', 'Avg Current Stock',
                       'Optimal Stock Level', 'Stock Status']

st.dataframe(season_opt, use_container_width=True)

# Visualization
fig8 = px.bar(
    season_opt,
    x='Category',
    y=['Avg Current Stock', 'Optimal Stock Level'],
    barmode='group',
    facet_col='Season',
    title='Current Stock vs Optimal Stock Level by Category and Season'
)
st.plotly_chart(fig8, use_container_width=True)

st.markdown("---")

# ============================================================
# LIVE REORDER RECOMMENDATIONS
# ============================================================
st.subheader("🚨 Live Reorder Recommendations")
st.markdown("Products that need to be reordered RIGHT NOW based on current stock levels")

live_reorder = filtered_df[filtered_df['reorder_alert'] == 'Yes'].groupby(
    ['store_id', 'product_id', 'category']
).agg(
    avg_inventory=('inventory_level', 'mean'),
    avg_daily_sales=('units_sold', 'mean'),
    avg_units_ordered=('units_ordered', 'mean')
).reset_index()

live_reorder['days_until_stockout'] = (
    live_reorder['avg_inventory'] / live_reorder['avg_daily_sales']
).round(1)

live_reorder['recommended_order_qty'] = (
    live_reorder['avg_daily_sales'] * 30
).round(0).astype(int)

live_reorder = live_reorder.sort_values('days_until_stockout').head(20)
live_reorder.columns = ['Store', 'Product', 'Category',
                         'Avg Inventory', 'Avg Daily Sales',
                         'Avg Units Ordered', 'Days Until Stockout',
                         'Recommended Order Qty']

st.dataframe(live_reorder, use_container_width=True)

st.markdown("---")
# ============================================================
# PHASE 5 — DEMAND FORECASTING (MOVING AVERAGE)
# ============================================================
st.subheader("📈 Demand Forecasting — Next 3 Months")
st.markdown("Based on historical sales patterns, predicting future demand using Moving Average method")

# Prepare monthly data
forecast_df = filtered_df.groupby('date').agg(
    actual_sales=('units_sold', 'sum')
).reset_index().sort_values('date')

# Calculate 3-month moving average for past data
forecast_df['moving_avg'] = forecast_df['actual_sales'].rolling(3).mean()

# Calculate MAE and RMSE
mae_df = forecast_df.dropna(subset=['moving_avg'])
mae = round((mae_df['actual_sales'] - mae_df['moving_avg']).abs().mean(), 2)
rmse = round(((mae_df['actual_sales'] - mae_df['moving_avg'])**2).mean()**0.5, 2)

col1, col2 = st.columns(2)
with col1:
    st.metric("MAE (Mean Absolute Error)", f"{mae} units")
with col2:
    st.metric("RMSE (Root Mean Square Error)", f"{rmse} units")

# Generate next 3 months forecast
last_3_avg = forecast_df['actual_sales'].tail(3).mean()
last_date = forecast_df['date'].max()

future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, 4)]
future_df = pd.DataFrame({
    'date': future_dates,
    'actual_sales': [None, None, None],
    'moving_avg': [None, None, None],
    'forecast': [round(last_3_avg, 0)] * 3
})

forecast_df['forecast'] = None
combined_df = pd.concat([forecast_df, future_df], ignore_index=True)

# Plot
fig9 = px.line(
    combined_df,
    x='date',
    y=['actual_sales', 'moving_avg', 'forecast'],
    title='Demand Forecast — Past Sales + Next 3 Months Prediction',
    labels={'value': 'Units Sold', 'date': 'Date'},
    color_discrete_map={
        'actual_sales': '#636EFA',
        'moving_avg': '#FFA15A',
        'forecast': '#00CC96'
    }
)
fig9.update_traces(
    selector=dict(name='forecast'),
    line=dict(dash='dot', width=3)
)
fig9.update_traces(
    selector=dict(name='actual_sales'),
    name='Actual Sales'
)
fig9.update_traces(
    selector=dict(name='moving_avg'),
    name='Moving Average'
)
fig9.update_traces(
    selector=dict(name='forecast'),
    name='3 Month Forecast'
)
st.plotly_chart(fig9, use_container_width=True)
st.info("ℹ️ Forecast is based on 3-Month Moving Average of historical sales. Lower MAE and RMSE indicate better prediction accuracy.")

st.markdown("---")

# ============================================================
# CSV DOWNLOAD BUTTON
# ============================================================
st.subheader("📥 Download Filtered Data")

csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Download Current Filtered Data as CSV",
    data=csv,
    file_name='filtered_inventory_data.csv',
    mime='text/csv'
)