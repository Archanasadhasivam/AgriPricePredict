import pandas as pd
from datetime import datetime, timedelta

# Load your CSV file (replace 'commodity_data.csv' with the actual filename if different)
try:
    df = pd.read_csv("commodity_data.csv")
except FileNotFoundError:
    print("Error: commodity_data.csv not found. Please make sure the file is in the correct directory.")
    exit()

# Clean up columns: remove leading/trailing whitespace
df.columns = df.columns.str.strip()

# Rename the first column to "Product Name" (assuming it's the product identifier)
if df.columns[0] != "Product Name":
    df = df.rename(columns={df.columns[0]: "Product Name"})

# Identify valid month columns (assuming format "Mon-YY" like "Jan-14")
valid_months = []
for col in df.columns[1:]:
    try:
        pd.to_datetime(col, format="%b-%y")
        valid_months.append(col)
    except ValueError:
        print(f"Warning: Skipping invalid month column '{col}'. Expected format 'Mon-YY'.")
        continue

# Create a cleaned DataFrame with only the product name and valid month columns
df_cleaned = df[["Product Name"] + valid_months]

# Melt the DataFrame from wide to long format
melted_df = df_cleaned.melt(id_vars=["Product Name"], var_name="Month", value_name="Price")

# Convert the "Month" column to datetime objects
try:
    melted_df["Month"] = pd.to_datetime(melted_df["Month"], format="%b-%y")
except ValueError:
    print("Error: Could not convert 'Month' column to datetime. Ensure the format is 'Mon-YY'.")
    exit()

# Filter data within the required date range
start_date = datetime(2014, 1, 1)
end_date = datetime(2024, 9, 30)
melted_df = melted_df[(melted_df["Month"] >= start_date) & (melted_df["Month"] <= end_date)].copy()

# Generate INSERT statements
insert_queries = []
for _, row in melted_df.iterrows():
    current_date = row["Month"].date()
    end_of_month = (row["Month"] + pd.offsets.MonthEnd(0)).date()
    product_name = row["Product Name"].replace("'", "''") # Escape single quotes in product name

    while current_date <= end_of_month:
        price = "NULL" if pd.isna(row["Price"]) else f"{row['Price']:.2f}"
        query = (
            f"INSERT INTO historical_prices (product_name, price, date) "
            f"VALUES ('{product_name}', {price}, '{current_date}');"
        )
        insert_queries.append(query)
        current_date += timedelta(days=1)

# Save the INSERT queries to an SQL file
output_filename = "insert_queries.sql"
with open(output_filename, "w") as file:
    file.write("\n".join(insert_queries))

print(f"Saved {len(insert_queries)} INSERT queries to '{output_filename}'")
