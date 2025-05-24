import pandas as pd
from datetime import datetime, timedelta

# Load your CSV
df = pd.read_csv("commodity_data.csv")

# Clean up columns
df.columns = df.columns.str.strip()
df = df.rename(columns={df.columns[0]: "Product Name"})

# Filter valid month columns
valid_months = []
for col in df.columns[1:]:
    try:
        pd.to_datetime(col, format="%b-%y")
        valid_months.append(col)
    except:
        continue

df_cleaned = df[["Product Name"] + valid_months]
melted_df = df_cleaned.melt(id_vars=["Product Name"], var_name="Month", value_name="Price")
melted_df["Month"] = pd.to_datetime(melted_df["Month"], format="%b-%y")

# Filter the required range
start_date = datetime(2014, 1, 1)
end_date = datetime(2024, 9, 30)
melted_df = melted_df[(melted_df["Month"] >= start_date) & (melted_df["Month"] <= end_date)]

# Generate INSERT statements
insert_queries = []
for _, row in melted_df.iterrows():
    current_date = row["Month"].date()
    end_of_month = (row["Month"] + pd.offsets.MonthEnd(0)).date()

    while current_date <= end_of_month:
        price = "NULL" if pd.isna(row["Price"]) else f"{row['Price']:.2f}"
        query = (
            f"INSERT INTO historical_prices (product_name, price, date) "
            f"VALUES ('{row['Product Name']}', {price}, '{current_date}');"
        )
        insert_queries.append(query)
        current_date += timedelta(days=1)

# Save to SQL file
with open("insert_queries.sql", "w") as file:
    file.write("\n".join(insert_queries))

print(f"Saved {len(insert_queries)} queries to insert_queries.sql")
