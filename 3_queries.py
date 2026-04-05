import pyodbc
import pandas as pd

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=Inventory_db;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
)

# Query 1 - Total units sold by category
q1 = pd.read_sql('''
    SELECT category, 
           SUM(units_sold) as total_units_sold,
           AVG(inventory_level) as avg_inventory
    FROM inventory
    GROUP BY category
    ORDER BY total_units_sold DESC
''', conn)
print("=== SALES BY CATEGORY ===")
print(q1)

# Query 2 - Low stock products needing reorder
q2 = pd.read_sql('''
    SELECT store_id, product_id, category, 
           AVG(inventory_level) as avg_inventory
    FROM inventory
    WHERE reorder_alert = 'Yes'
    GROUP BY store_id, product_id, category
    ORDER BY avg_inventory ASC
''', conn)
print("\n=== LOW STOCK PRODUCTS ===")
print(q2)

# Query 3 - Monthly sales trend
q3 = pd.read_sql('''
    SELECT FORMAT(date, 'yyyy-MM') as month,
           SUM(units_sold) as total_sold,
           SUM(units_ordered) as total_ordered
    FROM inventory
    GROUP BY FORMAT(date, 'yyyy-MM')
    ORDER BY month
''', conn)
print("\n=== MONTHLY SALES TREND ===")
print(q3)

# Query 4 - Sales by region
q4 = pd.read_sql('''
    SELECT region,
           SUM(units_sold) as total_sold,
           AVG(price) as avg_price
    FROM inventory
    GROUP BY region
    ORDER BY total_sold DESC
''', conn)
print("\n=== SALES BY REGION ===")
print(q4)

# Query 5 - Forecast accuracy
q5 = pd.read_sql('''
    SELECT category,
           AVG(demand_forecast) as avg_forecast,
           AVG(units_sold) as avg_actual,
           AVG(demand_forecast - units_sold) as avg_forecast_error
    FROM inventory
    GROUP BY category
''', conn)
print("\n=== FORECAST ACCURACY BY CATEGORY ===")
print(q5)

# Query 6 - Seasonal analysis
q6 = pd.read_sql('''
    SELECT seasonality,
           SUM(units_sold) as total_sold,
           AVG(inventory_level) as avg_inventory
    FROM inventory
    GROUP BY seasonality
    ORDER BY total_sold DESC
''', conn)
print("\n=== SALES BY SEASON ===")
print(q6)

conn.close()

# Export all to Excel
with pd.ExcelWriter('data/analysis.xlsx', engine='openpyxl') as writer:
    q1.to_excel(writer, sheet_name='Sales_by_Category', index=False)
    q2.to_excel(writer, sheet_name='Low_Stock', index=False)
    q3.to_excel(writer, sheet_name='Monthly_Trend', index=False)
    q4.to_excel(writer, sheet_name='Sales_by_Region', index=False)
    q5.to_excel(writer, sheet_name='Forecast_Accuracy', index=False)
    q6.to_excel(writer, sheet_name='Seasonal_Analysis', index=False)

print("\n✓ All queries exported to data/analysis.xlsx")
print("✓ Excel file has 6 sheets — one for each analysis")