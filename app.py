import pandas as pd
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
import joblib
from datetime import datetime  # ✅ Required for date validation
import os

app = Flask(__name__)
CORS(app)

# Configure session (optional, for user login)
# app.secret_key = 'your_secret_key'

# ✅ Database connection

    db = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "localhost"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "price_prediction"),
    port=int(os.environ.get("DB_PORT", 21436)) # Added 'port' parameter, defaulting to 3306


)
cursor = db.cursor()

# ✅ Load models and data
try:
    models = joblib.load("models.pkl")
except FileNotFoundError:
    print("⚠ Error: 'models.pkl' not found. Please run 'model.py' first to train the models.")
    models = {}

df = pd.read_csv("commodity_price.csv")
df.columns = df.columns.str.strip()

if "Commodities" in df.columns:
    print("✅ Products:", df["Commodities"].unique())
else:
    print("❌ 'Commodities' column not found in CSV!")

@app.route('/')
def home():
    return "Flask is working!"

# ---------------- USER AUTH ----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (data['username'], data['email'], data['password']))
        db.commit()
        return jsonify({"message": "User registered successfully!"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (data['email'], data['password']))
    user = cursor.fetchone()
    if user:
        # session['user_email'] = data['email']  # Uncomment if using sessions
        return jsonify({"message": "Login successful!"})
    return jsonify({"error": "Invalid credentials!"}), 401

# ---------------- HISTORICAL PRICE TRENDS ----------------
@app.route('/price_trend', methods=['GET'])
def get_price_trends():
    product = request.args.get('product_name')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    query = "SELECT date, price FROM historical_prices WHERE product_name=%s AND date BETWEEN %s AND %s"
    try:
        cursor.execute(query, (product, from_date, to_date))
        result = cursor.fetchall()

        if not result:
            return jsonify({"error": "Enter the correct date range!"})

        return jsonify([{"date": row[0].strftime('%Y-%m-%d'), "price": float(row[1])} for row in result])
    except Exception as e:
        return jsonify({"error": f"Error fetching price trends: {str(e)}"}), 500

# ---------------- PRICE PREDICTION ----------------
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    product = data.get('product')
    date_str = data.get('date')

    # ✅ Date validation
    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        if input_date < today:
            return jsonify({"error": "Enter correct date. Date cannot be in the past."}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # ✅ Check model existence
    if product not in models:
        return jsonify({"error": f"No model found for product: {product}"}), 400

    # ✅ Filter product data
    product_data = df[df["Commodities"] == product]
    if product_data.empty:
        return jsonify({"error": "No historical data found for this product!"}), 400

    # ✅ Extract latest price column
    price_columns = [col for col in df.columns if '-' in col and len(col.split('-')[1]) == 2]
    if not price_columns:
        return jsonify({"error": "Not enough price data columns in the CSV!"}), 400

    latest_price_col = price_columns[-1]
    if latest_price_col not in product_data.columns or pd.isna(product_data[latest_price_col].iloc[0]):
        return jsonify({"error": f"Latest price data not available for {product}."}), 400

    latest_price = product_data[latest_price_col].iloc[0]
    prediction_input = [[latest_price]]

    try:
        model = models[product]
        predicted_price = model.predict(prediction_input)[0]
        predicted_price_mysql = float(round(predicted_price, 2))

        # ✅ Store in database
        cursor.execute(
            "INSERT INTO price_predictions (product_name, predicted_price, prediction_date) VALUES (%s, %s, %s)",
            (product, predicted_price_mysql, date_str))
        db.commit()

        return jsonify({"predicted_price": predicted_price_mysql})
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(debug=True)

