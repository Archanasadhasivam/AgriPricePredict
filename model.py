import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import numpy as np

# ✅ Load the dataset
df = pd.read_csv("commodity_price.csv")

# ✅ Clean column names (remove spaces)
df.columns = df.columns.str.strip()

# ✅ Check for 'Commodities' column
if 'Commodities' not in df.columns:
    raise ValueError("❌ 'Commodities' column not found in CSV!")

# ✅ Identify price columns (all except 'Commodities')
price_columns = [col for col in df.columns if col != 'Commodities']

if len(price_columns) < 2:
    raise ValueError("❌ Need at least 2 months of price data to train the model.")

# ✅ Ensure price columns are numeric, coerce errors to NaN
df[price_columns] = df[price_columns].apply(pd.to_numeric, errors='coerce')

# ✅ Train a model for each commodity
models = {}
for commodity in df['Commodities'].unique():
    commodity_df = df[df['Commodities'] == commodity].copy()

    # ✅ Select available price columns for the current commodity, removing NaN columns
    valid_price_cols = [col for col in price_columns if not commodity_df[col].isnull().all()]

    if len(valid_price_cols) >= 2:
        # ✅ Use the last two valid price columns for training
        last_price_col = valid_price_cols[-1]
        second_last_price_col = valid_price_cols[-2]

        # ✅ Drop rows where the second last price is NaN
        not_nan_second_last = commodity_df[second_last_price_col].dropna()
        X = not_nan_second_last.values.reshape(-1, 1)
        y = commodity_df.loc[not_nan_second_last.index, last_price_col].dropna().values

        # ✅ Check if there's enough data to train *after* dropping NaNs
        if len(X) > 0 and len(y) > 0 and len(X) == len(y):
            # ✅ Train model for this commodity
            model = LinearRegression()
            model.fit(X, y)
            models[commodity] = model
            print(f"✅ Model trained for {commodity} with {len(X)} data points.")
        else:
            print(f"⚠️ Insufficient consecutive data to train model for {commodity}.")
    else:
        print(f"⚠️ Less than 2 valid price points for {commodity}.")

# ✅ Save the trained models
joblib.dump(models, "models.pkl")
print("✅ All models training process completed. Check messages for trained models.")