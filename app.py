import pandas as pd
from flask import Flask, request, jsonify, session, render_template
from flask_cors import CORS
import mysql.connector
import joblib
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Optional: Configure session (uncomment if needed)
# app.secret_key = 'your_very_secret_and_long_random_key_here'

# ✅ Database connection using Aiven
db = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "mysql-fc0e3b0-sadhasivamkanaga15-f154.l.aivencloud.com"),
    user=os.environ.get("DB_USER", "avnadmin"),
    password=os.environ.get("DB_PASSWORD", "AVNS_P2X1P7jH__WuLtv9YSs"),
    database=os.environ.get("DB_NAME", "defaultdb"),
    port=int(os.environ.get("DB_PORT", 21436))
)
cursor = db.cursor()

# ✅ Load machine learning models
try:
    models = joblib.load("models.pkl")
except FileNotFoundError:
    print("⚠ Error: 'models.pkl' not found. Please run 'model.py' to train and save models.")
    models = {}

# ✅ Load CSV
df = pd.read_csv("commodity_price.csv")
df.columns = df.columns.str.strip()

if "Commodities" in df.columns:
    print("✅ Products loaded:", df["Commodities"].unique())
else:
    print("❌ 'Commodities' column not found in the CSV.")

# ---------------- HOME ROUTE ----------------
@app.route('/')
def home():
    return render_template('login.php')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({"error": "Missing registration data."}), 400

    hashed_password = generate_password_hash(password)

    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (username, email, hashed_password))
        db.commit()
        return jsonify({"message": "User registered successfully!"})
    except Exception as e:
        db.rollback()
        print(f"Registration error: {e}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"error": "Email and password are required."}), 400

    cursor.execute("SELECT id, email, password FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user[2], password):
        return jsonify({"message": "Login successful!"})
    return jsonify({"error": "Invalid credentials!"}), 401

# ---------------- PRICE TREND ----------------
@app.route('/price_trend', methods=['GET'])
def get_price_trends():
    product = request.args.get('product_name')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    if not all([product, from_date, to_date]):
        return jsonify({"error": "Product name, from_date, and to_date are required."}), 400

    query = "SELECT date, price FROM historical_prices WHERE product_name=%s AND date BETWEEN %s AND %s"
    try:
        cursor.execute(query, (product, from_date, to_date))
        result = cursor.fetchall()

        if not result:
            return jsonify({"error": "No historical data found for the specified product and date range. Enter the correct date range!"})

        return jsonify([
            {"date": row[0].strftime('%Y-%m-%d'), "price": float(row[1])} for row in result
        ])
    except Exception as e:
        print(f"Error fetching price trends: {e}")
        return jsonify({"error": f"Error fetching price trends: {str(e)}"}), 500

# ---------------- PREDICTION ----------------
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    product = data.get('product')
    date_str = data.get('date')

    if not all([product, date_str]):
        return jsonify({"error": "Product and date are required for prediction."}), 400

    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        if input_date < today:
            return jsonify({"error": "Enter correct date. Prediction date cannot be in the past."}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if product not in models:
        return jsonify({"error": f"No prediction model found for product: {product}. Please train the model."}), 400

    product_data = df[df["Commodities"] == product]
    if product_data.empty:
        return jsonify({"error": "No historical data found in CSV for this product to make a prediction!"}), 400

    price_columns = [col for col in df.columns if '-' in col and len(col.split('-')[1]) == 2]
    if not price_columns:
        return jsonify({"error": "Not enough price data columns in the CSV for prediction!"}), 400

    latest_price_col = price_columns[-1]

    if latest_price_col not in product_data.columns or pd.isna(product_data[latest_price_col].iloc[0]):
        return jsonify({"error": f"Latest price data not available in CSV for {product} to make a prediction."}), 400

    latest_price = product_data[latest_price_col].iloc[0]
    prediction_input = [[latest_price]]

    try:
        model = models[product]
        predicted_price = model.predict(prediction_input)[0]
        predicted_price_mysql = float(round(predicted_price, 2))

        cursor.execute(
            "INSERT INTO price_predictions (product_name, predicted_price, prediction_date) VALUES (%s, %s, %s)",
            (product, predicted_price_mysql, date_str)
        )
        db.commit()

        return jsonify({"predicted_price": predicted_price_mysql})
    except Exception as e:
        db.rollback()
        print(f"Error during prediction: {e}")
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("✅ Starting Flask app...")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
