import pandas as pd
import pyodbc

df = pd.read_csv('data/cleaned_data.csv')

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=Inventory_db;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
)

cursor = conn.cursor()

cursor.execute('''
    IF OBJECT_ID('inventory', 'U') IS NOT NULL
        DROP TABLE inventory
''')

cursor.execute('''
    CREATE TABLE inventory (
        date DATE,
        store_id VARCHAR(10),
        product_id VARCHAR(10),
        category VARCHAR(50),
        region VARCHAR(20),
        inventory_level INT,
        units_sold INT,
        units_ordered INT,
        demand_forecast FLOAT,
        price FLOAT,
        discount INT,
        weather_condition VARCHAR(20),
        holiday_promotion INT,
        competitor_pricing FLOAT,
        seasonality VARCHAR(20),
        reorder_alert VARCHAR(5)
    )
''')

print("✓ Table created successfully")

for index, row in df.iterrows():
    cursor.execute('''
        INSERT INTO inventory VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', tuple(row))

conn.commit()
conn.close()

print(f"✓ {len(df)} rows inserted into Inventory_db")
print("✓ Database loading complete!")