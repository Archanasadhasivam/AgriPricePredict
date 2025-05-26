import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import numpy as np

# ✅ Load the dataset
# Ensure 'commodity_price.csv' is in the same directory as this script,
# or provide the full path to the file.
try:
    df = pd.read_csv("commodity_price.csv")
except FileNotFoundError:
    raise FileNotFoundError("❌ 'commodity_price.csv' not found. Please ensure the CSV file is in the correct directory.")

# ✅ Clean column names (remove leading/trailing spaces)
df.columns = df.columns.str.strip()

# ✅ Check for 'Commodities' column, which is expected to identify each product
if 'Commodities' not in df.columns:
    raise ValueError("❌ 'Commodities' column not found in CSV! This column is essential for identifying products.")

# ✅ Identify price columns: all columns except the 'Commodities' column
price_columns = [col for col in df.columns if col != 'Commodities']

# ✅ Ensure there's enough price data to train a model (at least 2 months)
if len(price_columns) < 2:
    raise ValueError("❌ Need at least 2 months of price data (columns) in the CSV to train the model.")

# ✅ Ensure price columns are numeric. Coerce non-numeric values to NaN (Not a Number).
# This prevents errors during numerical operations if there are non-numeric entries.
df[price_columns] = df[price_columns].apply(pd.to_numeric, errors='coerce')

# ✅ Initialize an empty dictionary to store the trained models
models = {}

# ✅ Iterate through each unique commodity to train a separate model
for commodity in df['Commodities'].unique():
    # Create a copy of the DataFrame for the current commodity to avoid SettingWithCopyWarning
    commodity_df = df[df['Commodities'] == commodity].copy()

    # ✅ Select available price columns for the current commodity.
    # We remove columns where all values are NaN for this specific commodity,
    # as they contain no useful data for training.
    valid_price_cols = [col for col in price_columns if not commodity_df[col].isnull().all()]

    # ✅ Check if there are at least two valid price columns for the current commodity
    if len(valid_price_cols) >= 2:
        # ✅ Use the last two valid price columns for training.
        # This approach assumes a time-series dependency where the current price
        # is predicted based on the previous price.
        last_price_col = valid_price_cols[-1]
        second_last_price_col = valid_price_cols[-2]

        # ✅ Prepare the features (X) and target (y) for the model.
        # X will be the second-to-last valid price, and y will be the last valid price.
        # Drop NaN values from the 'second_last_price_col' to ensure valid training data.
        not_nan_second_last = commodity_df[second_last_price_col].dropna()
        X = not_nan_second_last.values.reshape(-1, 1) # Reshape for sklearn (requires 2D array)
        y = commodity_df.loc[not_nan_second_last.index, last_price_col].dropna().values

        # ✅ Final check to ensure there's enough aligned data points for training.
        # Both X and y must have data and be of the same length.
        if len(X) > 0 and len(y) > 0 and len(X) == len(y):
            # ✅ Train a Linear Regression model for this commodity
            model = LinearRegression()
            model.fit(X, y)
            models[commodity] = model # Store the trained model in the dictionary
            print(f"✅ Model trained for '{commodity}' with {len(X)} data points.")
        else:
            print(f"⚠️ Insufficient consecutive non-NaN data points to train model for '{commodity}'. Skipping.")
    else:
        print(f"⚠️ Less than 2 valid (non-NaN) price points found for '{commodity}'. Skipping model training for this commodity.")

# ✅ Save all the trained models to a file named "models.pkl".
# This file can then be loaded by your Flask application for predictions.
joblib.dump(models, "models.pkl")
print(f"✅ All model training processes completed. Trained models saved to 'models.pkl'.")
print("   Please ensure 'models.pkl' is included in your deployment package (e.g., GitHub repository for Render).")
