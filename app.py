import pandas as pd
from flask import Flask, request, jsonify, render_template, session, url_for, redirect
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

# ---------------- SIGNUP PAGE ROUTE ----------------
@app.route('/signup.html')
def signup_page():
    return render_template('signup.html') # Assuming you have a signup.html template

# ---------------- ADMIN LOGIN PAGE ROUTE ----------------
@app.route('/admin_login.html')
def admin_login_page():
    return render_template('admin_login.html') # Assuming you have an admin_login.html template

# ---------------- USER REGISTRATION ROUTE ----------------
@app.route('/register', methods=['POST'])
def register():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    cursor = conn.cursor()
    data = request.form # Changed from request.json to request.form for HTML forms
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        cursor.close()
        conn.close()
        return render_template('signup.html', error="Missing registration data.") # Render template with error

    hashed_password = generate_password_hash(password)

    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (username, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        session['registration_success'] = "Registration successful! You can now log in."
        return redirect(url_for('login_page')) # Redirect to login page
    except mysql.connector.IntegrityError as err:
        conn.rollback()
        cursor.close()
        conn.close()
        if "Duplicate entry" in str(err) and "email" in str(err):
            return render_template('signup.html', error="Email address is already registered.") # Render template with error
        else:
            print(f"Registration error: {err}")
            return render_template('signup.html', error=f"Registration failed: {str(err)}") # Render template with error
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"Registration error: {e}")
        return render_template('signup.html', error=f"Registration failed: {str(e)}") # Render template with error

# ---------------- USER LOGIN ROUTE ----------------
@app.route('/login', methods=['POST'])
def login():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed."}), 500
    cursor = conn.cursor()
    data = request.form # Changed from request.json to request.form for HTML forms
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        cursor.close()
        conn.close()
        return render_template('login.html', error="Email and password are required.") # Render template with error

    cursor.execute("SELECT id, email, password, username FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        user_id, user_email, hashed_password_from_db, username = user # Added username to unpacking
        if check_password_hash(hashed_password_from_db, password):
            session['user_email'] = user_email
            session['user_id'] = user_id
            session['username'] = username # Store username in session
            return redirect(url_for('dashboard')) # Redirect to dashboard on successful login
        else:
            return render_template('login.html', error="Invalid credentials!") # Render template with error
    return render_template('login.html', error="Invalid credentials!") # Render template with error

# ---------------- ADMIN LOGIN API ROUTE ----------------
@app.route('/admin_login', methods=['POST'])
def admin_login():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    data = request.form # Changed from request.json to request.form for HTML forms
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        conn.close()
        return render_template('admin_login.html', error='Email and Password are required!')

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, password FROM admin_users WHERE email = %s", (email,))
        admin_user = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin_user and check_password_hash(admin_user['password'], password):
            session['admin_id'] = admin_user['id']
            session['admin_email'] = admin_user['email']
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard')) # Redirect to admin dashboard
        else:
            return render_template('admin_login.html', error='Invalid admin credentials!')
    except mysql.connector.Error as err:
        conn.close()
        return render_template('admin_login.html', error=f"Database error during admin login: {err}")

# ---------------- DASHBOARD ROUTE ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        # Fetch user details for dashboard display
        conn = get_db_connection()
        if not conn:
            return "Database connection failed", 500
        cursor = conn.cursor(dictionary=True)
        user_email = session['user_email']
        username = session.get('username', 'User') # Get username from session

        alerts = []
        try:
            cursor.execute("SELECT id, product_name, alert_price FROM price_alerts WHERE user_id = %s", (session['user_id'],))
            alerts = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error fetching alerts for dashboard: {err}")
        finally:
            cursor.close()
            conn.close()

        return render_template('dashboard.html', user_email=user_email, username=username, alerts=alerts)
    else:
        return redirect(url_for('login_page')) # Redirect to login if not logged in

# ---------------- ADMIN DASHBOARD ROUTE ----------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'is_admin' in session and session['is_admin']:
        conn = get_db_connection()
        if not conn:
            return "Database connection failed", 500

        users = []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, email FROM users") # Fetching from 'users' table
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return render_template('admin_dashboard.html', users=users, message=session.pop('message', None), message_type=session.pop('message_type', None))
        except mysql.connector.Error as err:
            conn.close()
            return f"Database error: {err}", 500
    else:
        return redirect(url_for('admin_login_page')) # Redirect to admin login if not admin

# ---------------- DELETE USER (ADMIN) ROUTE ----------------
@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('admin_login_page'))

    conn = get_db_connection()
    if not conn:
        session['message'] = "Database connection failed.";
        session['message_type'] = 'danger';
        return redirect(url_for('admin_dashboard'))

    try:
        cursor = conn.cursor()
        delete_query = "DELETE FROM users WHERE id = %s"
        cursor.execute(delete_query, (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        session['message'] = "User deleted successfully.";
        session['message_type'] = 'success';
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        session['message'] = f"Error deleting user: {err}";
        session['message_type'] = 'danger';

    return redirect(url_for('admin_dashboard'))

# ---------------- PREDICT PRICE PAGE ROUTE ----------------
@app.route('/predict_price')
def predict_price_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    products = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT product_name FROM historical_prices ORDER BY product_name ASC")
        product_results = cursor.fetchall()
        products = [row[0] for row in product_results]
        cursor.close()
    except mysql.connector.Error as err:
        conn.close()
        return f"Database error fetching products: {err}", 500
    finally:
        if conn and conn.is_connected():
            conn.close()

    return render_template('predict_price.html', products=products)

# ---------------- PRICE PREDICTION API ROUTE ----------------
@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized. Please log in."}), 401 # Return JSON for API calls

    if not models:
        return jsonify({"error": "Prediction models are not loaded. Please ensure 'models.pkl' exists and was trained."}), 503

    data = request.form # Changed from request.json to request.form for HTML forms
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

# ---------------- ALERT SETTINGS PAGE ROUTE ----------------
@app.route('/alert_settings')
def alert_settings_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    alerts = []
    products = []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, product_name, alert_price FROM price_alerts WHERE user_id = %s", (user_id,))
        alerts = cursor.fetchall()

        cursor.execute("SELECT DISTINCT product_name FROM historical_prices ORDER BY product_name ASC")
        product_results = cursor.fetchall()
        products = [row['product_name'] for row in product_results] # Assuming dictionary=True for products too
    except mysql.connector.Error as err:
        print(f"Error fetching alerts or products: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('alert_settings.html', alerts=alerts, products=products, message=session.pop('alert_message', None))

# ---------------- SET/UPDATE ALERT ROUTE ----------------
@app.route('/set_alert', methods=['POST'])
def set_alert():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized. Please log in."}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    product = request.form.get('product')
    price = request.form.get('price')

    if not product or not price:
        conn.close()
        session['alert_message'] = "Please fill in all fields!"
        return redirect(url_for('alert_settings_page'))

    try:
        price = float(price) # Ensure price is a float
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM price_alerts WHERE user_id = %s AND product_name = %s", (user_id, product))
        existing_alert = cursor.fetchone()

        if existing_alert:
            update_query = "UPDATE price_alerts SET alert_price = %s WHERE id = %s"
            cursor.execute(update_query, (price, existing_alert[0]))
            conn.commit()
            session['alert_message'] = "Alert updated successfully!"
        else:
            insert_query = "INSERT INTO price_alerts (user_id, product_name, alert_price) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (user_id, product, price))
            conn.commit()
            session['alert_message'] = "Alert set successfully!"
        cursor.close()
    except ValueError:
        session['alert_message'] = "Invalid price value."
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database error setting alert: {err}")
        session['alert_message'] = f"Error setting alert: {err}"
    finally:
        if conn and conn.is_connected():
            conn.close()

    return redirect(url_for('alert_settings_page'))

# ---------------- DELETE ALERT ROUTE ----------------
@app.route('/alerts/delete/<int:alert_id>')
def delete_alert(alert_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        session['alert_message'] = "Database connection failed."
        return redirect(url_for('alert_settings_page'))

    try:
        cursor = conn.cursor()
        delete_query = "DELETE FROM price_alerts WHERE id = %s AND user_id = %s"
        cursor.execute(delete_query, (alert_id, user_id))
        conn.commit()
        cursor.close()
        session['alert_message'] = "Alert deleted successfully!"
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database error deleting alert: {err}")
        session['alert_message'] = f"Error deleting alert: {err}"
    finally:
        if conn and conn.is_connected():
            conn.close()
    return redirect(url_for('alert_settings_page'))

# ---------------- HISTORICAL PRICE PAGE ROUTE ----------------
@app.route('/historical_price')
def historical_price_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    products = []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT product_name FROM historical_prices ORDER BY product_name ASC")
        product_results = cursor.fetchall()
        products = [row['product_name'] for row in product_results]
    except mysql.connector.Error as err:
        print(f"Database error fetching products for historical price: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('historical_price.html', products=products)

# ---------------- LOGOUT ROUTE ----------------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('username', None) # Clear username from session
    session.pop('admin_id', None) # Clear admin session if exists
    session.pop('admin_email', None)
    session.pop('is_admin', None)
    return redirect(url_for('loggedout_page')) # Redirect to the logged out page

# ---------------- LOGGED OUT PAGE ROUTE ----------------
@app.route('/loggedout.html')
def loggedout_page():
    return render_template('loggedout.html')

# ---------------- RUN THE FLASK APPLICATION ----------------
if __name__ == "__main__":
    print("✅ Starting Flask app...")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
