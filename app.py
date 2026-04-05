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
    return df

df = load_data()

st.title("📦 Intelligent Inventory Optimization System")
st.markdown("---")

st.sidebar.title("Filters")
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

filtered_df = df[(df['category'].isin(category)) & (df['region'].isin(region))]

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
st.subheader("Low Stock Alert")
low_stock = filtered_df[filtered_df['reorder_alert'] == 'Yes'][
    ['store_id', 'product_id', 'category', 'inventory_level']
].drop_duplicates().sort_values('inventory_level').head(20)
st.dataframe(low_stock, use_container_width=True)