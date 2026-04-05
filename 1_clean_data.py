import pandas as pd

df = pd.read_csv('data/raw_data.csv')

print("=== RAW DATA OVERVIEW ===")
print(f"Total rows    : {len(df)}")
print(f"Total columns : {len(df.columns)}")
print(f"\nColumn names:\n{list(df.columns)}")
print(f"\nFirst 3 rows:\n{df.head(3)}")

print("\n=== CHECKING FOR NULLS ===")
print(df.isnull().sum())

print("\n=== DATA TYPES ===")
print(df.dtypes)

df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

df['date'] = pd.to_datetime(df['date'])

df['category'] = df['category'].str.strip()
df['region'] = df['region'].str.strip()
df['weather_condition'] = df['weather_condition'].str.strip()
df['seasonality'] = df['seasonality'].str.strip()

df['reorder_alert'] = df['inventory_level'].apply(lambda x: 'Yes' if x < 100 else 'No')

print("\n=== CLEANED COLUMN NAMES ===")
print(list(df.columns))

print("\n=== SAMPLE CLEANED DATA ===")
print(df.head(3))

df.to_csv('data/cleaned_data.csv', index=False)
print("\n✓ Cleaned data saved to data/cleaned_data.csv")
print(f"✓ Total rows in cleaned file: {len(df)}")