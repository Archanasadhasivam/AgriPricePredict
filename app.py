import pandas as pd
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_cors import CORS
import mysql.connector
import joblib
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# ✅ Session secret key
app.secret_key = 'your_very_secret_and_long_random_key_here'  # Replace with a secure key in production

# ✅ Database connection
db = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "mysql-fc0e3b0-sadhasivamkanaga15-f154.l.aivencloud.com"),
    user=os.environ.get("DB_USER", "avnadmin"),
    password=os.environ.get("DB_PASSWORD", "AVNS_P2X1P7jH__WuLtv9YSs"),
    database=os.environ.get("DB_NAME", "defaultdb"),
    port=int(os.environ.get("DB_PORT", 21436))
)
cursor = db.cursor()

# ✅ Load ML models
try:
    models = joblib.load("models.pkl")
except FileNotFoundError:
    print("⚠ Error: 'models.pkl' not found.")
    models = {}

# ✅ Load CSV
df = pd.read_csv("commodity_price.csv")
df.columns = df.columns.str.strip()

# ---------------- HOME ROUTE ----------------
@app.route('/')
def home():
    return render_template('login.html')

# ---------------- DASHBOARD ROUTE ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return f"Welcome, user ID {session['user_id']}! <a href='/logout'>Logout</a>"
    return redirect(url_for('home'))

# ---------------- LOGOUT ROUTE ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ---------------- REGISTER ROUTE ----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username, email, password = data.get('username'), data.get('email'), data.get('password')

    if not all([username, email, password]):
        return jsonify({"error": "Missing registration data."}), 400

    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (username, email, password))
        db.commit()
        return jsonify({"message": "User registered successfully!"})
    except Exception as e:
        db.rollback()
        print(f"Registration error: {e}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

# ---------------- LOGIN ROUTE ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email, password = data.get('email'), data.get('password')

    if not all([email, password]):
        return jsonify({"error": "Email and password are required."}), 400

    cursor.execute("SELECT id, email, password FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user and password == user[2]:
        session['user_email'] = email
        session['user_id'] = user[0]
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
            return jsonify({"error": "No historical data found."})
        return jsonify([{"date": row[0].strftime('%Y-%m-%d'), "price": float(row[1])} for row in result])
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"{str(e)}"}), 500

# ---------------- PRICE PREDICTION ----------------
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    product = data.get('product')
    date_str = data.get('date')

    if not all([product, date_str]):
        return jsonify({"error": "Product and date are required."}), 400

    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if input_date < datetime.today().date():
            return jsonify({"error": "Prediction date cannot be in the past."}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if product not in models:
        return jsonify({"error": f"No prediction model found for product: {product}."}), 400

    product_data = df[df["Commodities"] == product]
    price_columns = [col for col in df.columns if '-' in col and len(col.split('-')[1]) == 2]
    if not price_columns:
        return jsonify({"error": "No usable price columns in CSV."}), 400

    latest_price_col = price_columns[-1]
    if pd.isna(product_data[latest_price_col].iloc[0]):
        return jsonify({"error": "Latest price data missing."}), 400

    latest_price = product_data[latest_price_col].iloc[0]
    try:
        predicted_price = models[product].predict([[latest_price]])[0]
        cursor.execute(
            "INSERT INTO price_predictions (product_name, predicted_price, prediction_date) VALUES (%s, %s, %s)",
            (product, round(predicted_price, 2), date_str)
        )
        db.commit()
        return jsonify({"predicted_price": round(predicted_price, 2)})
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"{str(e)}"}), 500

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    print("✅ Starting Flask app...")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
