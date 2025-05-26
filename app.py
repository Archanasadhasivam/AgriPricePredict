import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import joblib
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Configure session (important for secure login)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_very_secret_and_long_random_key_here")

# ✅ Database connection using Aiven details from environment variables
db_host = os.environ.get("DB_HOST", "mysql-fc0e3b0-sadhasivamkanaga15-f154.l.aivencloud.com")
db_user = os.environ.get("DB_USER", "avnadmin")
db_password = os.environ.get("DB_PASSWORD", "AVNS_P2X1P7jH__WuLtv9YSs")
db_name = os.environ.get("DB_NAME", "defaultdb")
db_port = int(os.environ.get("DB_PORT", 21436))

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# ✅ Load machine learning models
models = {}
try:
    models = joblib.load("models.pkl")
    print("✅ Machine learning models loaded successfully.")
except FileNotFoundError:
    print("⚠ Error: 'models.pkl' not found. Please run 'model.py' to train and save models.")
except Exception as e:
    print(f"⚠ Error loading models: {e}")

# ✅ Load commodity data from CSV
try:
    df = pd.read_csv("commodity_price.csv")
    df.columns = df.columns.str.strip() # Clean column names
    if "Commodities" in df.columns:
        print("✅ Products loaded:", df["Commodities"].unique())
    else:
        print("❌ 'Commodities' column not found in the CSV. Please check 'commodity_price.csv'.")
        df = pd.DataFrame() # Initialize empty DataFrame to avoid errors later
except FileNotFoundError:
    print("❌ Error: 'commodity_price.csv' not found.")
    df = pd.DataFrame()
except Exception as e:
    print(f"❌ Error loading commodity data: {e}")
    df = pd.DataFrame()

# ---------------- HOME ROUTE ----------------
@app.route('/')
def home():
    return render_template('login.html') # Assuming you have a login.html template

# ---------------- USER REGISTRATION ROUTE ----------------
@app.route('/register', methods=['POST'])
def register():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    cursor = conn.cursor()
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        cursor.close()
        conn.close()
        return jsonify({"error": "Missing registration data."}), 400

    hashed_password = generate_password_hash(password)

    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (username, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "User registered successfully!"})
    except mysql.connector.IntegrityError as err:
        conn.rollback()
        cursor.close()
        conn.close()
        if "Duplicate entry" in str(err) and "email" in str(err):
            return jsonify({"error": "Email address is already registered."}), 409
        else:
            print(f"Registration error: {err}")
            return jsonify({"error": f"Registration failed: {str(err)}"}), 500
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Registration error: {e}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

# ---------------- USER LOGIN ROUTE ----------------
@app.route('/login', methods=['POST'])
def login():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    cursor = conn.cursor()
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        cursor.close()
        conn.close()
        return jsonify({"error": "Email and password are required."}), 400

    cursor.execute("SELECT id, email, password FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        user_id, user_email, hashed_password_from_db = user
        if check_password_hash(hashed_password_from_db, password):
            session['user_email'] = user_email
            session['user_id'] = user_id
            return jsonify({"message": "Login successful!"})
        else:
            return jsonify({"error": "Invalid credentials!"}), 401
    return jsonify({"error": "Invalid credentials!"}), 401

# ---------------- PRICE TREND FETCH ROUTE ----------------
@app.route('/price_trend', methods=['GET'])
def get_price_trends():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    cursor = conn.cursor()
    product = request.args.get('product_name')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    if not all([product, from_date, to_date]):
        cursor.close()
        conn.close()
        return jsonify({"error": "Product name, from_date, and to_date are required."}), 400

    query = "SELECT date, price FROM historical_prices WHERE product_name=%s AND date BETWEEN %s AND %s"
    try:
        cursor.execute(query, (product, from_date, to_date))
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        if not result:
            return jsonify({"error": "No historical data found for the specified product and date range. Enter the correct date range!"})

        return jsonify([
            {"date": row[0].strftime('%Y-%m-%d'), "price": float(row[1])} for row in result
        ])
    except Exception as e:
        print(f"Error fetching price trends: {e}")
        cursor.close()
        conn.close()
        return jsonify({"error": f"Error fetching price trends: {str(e)}"}), 500

# ---------------- PRICE PREDICTION ROUTE ----------------
@app.route('/predict', methods=['POST'])
def predict():
    if not models:
        return jsonify({"error": "Prediction models are not loaded. Please ensure 'models.pkl' exists and was trained."}), 503

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
        return jsonify({"error": f"No prediction model found for product: {product}. Please ensure the model was trained."}), 400

    if df.empty or "Commodities" not in df.columns:
        return jsonify({"error": "Commodity data CSV not loaded properly."}), 500

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

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "INSERT INTO price_predictions (product_name, predicted_price, prediction_date) VALUES (%s, %s, %s)"
            cursor.execute(query, (product, predicted_price_mysql, date_str))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"predicted_price": predicted_price_mysql})
        else:
            return jsonify({"predicted_price": predicted_price_mysql, "warning": "Could not save prediction to database."}), 200

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500

# ---------------- RUN THE FLASK APPLICATION ----------------
if __name__ == "__main__":
    print("✅ Starting Flask app...")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
