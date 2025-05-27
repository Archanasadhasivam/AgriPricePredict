import pandas as pd
from flask import Flask, request, jsonify, render_template, session, url_for, redirect
from flask_cors import CORS
import mysql.connector
import joblib
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

# Configure session (important for secure login)
# IMPORTANT: Replace "your_very_secret_and_long_random_key_here" with a strong, random key
# For production, set this as an environment variable in Render.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_very_secure_and_long_random_string_for_flask_session_keys_1234567890")

# ✅ Database connection details from environment variables (using Aiven details as per original request)
# These should be set in your Render service environment variables.
# The hardcoded values are for local testing/defaults if env vars are not set.
db_host = os.environ.get("DB_HOST", "mysql-fc0e3b0-sadhasivamkanaga15-f154.l.aivencloud.com")
db_user = os.environ.get("DB_USER", "avnadmin")
db_password = os.environ.get("DB_PASSWORD", "AVNS_P2X1P7jH__WuLtv9YSs") # Replace with your actual Aiven password!
db_name = os.environ.get("DB_NAME", "defaultdb")
db_port = int(os.environ.get("DB_PORT", 21436))

def get_db_connection():
    """Establishes and returns a new database connection."""
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port
            # ssl_ca='path/to/your/aiven_ca.pem' # Uncomment and provide path if Aiven requires SSL CA file
        )
        logging.info("✅ Database connection established (get_db_connection).")
        return conn
    except mysql.connector.Error as err:
        logging.error(f"❌ Database connection error (get_db_connection): {err}")
        return None

# Helper function to get product list from DB
def get_product_list():
    """Fetches a distinct list of product names from the historical_prices table."""
    conn = get_db_connection()
    if not conn:
        logging.error("❌ get_product_list: Database connection failed.")
        return []
    
    products = []
    try:
        cursor = conn.cursor(dictionary=True) # Use dictionary=True for easier access by column name
        cursor.execute("SELECT DISTINCT product_name FROM historical_prices ORDER BY product_name ASC")
        product_results = cursor.fetchall()
        products = [row['product_name'] for row in product_results]
        logging.info(f"✅ get_product_list: Fetched {len(products)} products.")
    except mysql.connector.Error as err:
        logging.error(f"❌ get_product_list: Database error fetching products: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return products

# ✅ Load machine learning models
models = {}
try:
    models = joblib.load("models.pkl")
    logging.info("✅ Machine learning models loaded successfully.")
except FileNotFoundError:
    logging.warning("⚠ Error: 'models.pkl' not found. Please run 'model.py' to train and save models.")
except Exception as e:
    logging.error(f"⚠ Error loading models: {e}")

# ✅ Load commodity data from CSV
df = pd.DataFrame() # Initialize as empty DataFrame
try:
    df = pd.read_csv("commodity_price.csv")
    df.columns = df.columns.str.strip() # Clean column names
    if "Commodities" in df.columns:
        logging.info("✅ Products loaded from CSV: %s", df["Commodities"].unique())
    else:
        logging.error("❌ 'Commodities' column not found in 'commodity_price.csv'. Please check the CSV structure.")
        df = pd.DataFrame() # Ensure df is empty if column is missing
except FileNotFoundError:
    logging.error("❌ Error: 'commodity_price.csv' not found.")
except Exception as e:
    logging.error(f"❌ Error loading commodity data from CSV: {e}")
    df = pd.DataFrame()

# ---------------- HOME ROUTE ----------------
@app.route('/')
def home():
    """Renders the login page as the default home page."""
    return render_template('login.html')

# ---------------- SIGNUP PAGE ROUTE ----------------
@app.route('/signup.html')
def signup_page():
    """Renders the signup HTML page."""
    error_message = request.args.get('error')
    return render_template('signup.html', error=error_message)

# ---------------- ADMIN LOGIN PAGE ROUTE ----------------
@app.route('/admin_login.html')
def admin_login_page():
    """Renders the admin login HTML page."""
    error_message = request.args.get('error')
    return render_template('admin_login.html', error=error_message)

# ---------------- USER REGISTRATION ROUTE ----------------
@app.route('/register', methods=['POST'])
def register():
    """Handles new user registration."""
    conn = get_db_connection()
    if not conn:
        logging.error("❌ Register: Database connection failed (at the beginning of route).")
        return jsonify({"status": "error", "message": "Database connection failed. Please try again later."}), 500

    cursor = conn.cursor()
    data = request.form # Assuming signup form still uses standard form submission
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    logging.debug("ℹ️ Register: Form data received: %s", data)
    logging.info(f"ℹ️ Register: Attempting to register Username: '{username}', Email: '{email}', Password (length): {len(password) if password else 0}")

    if not all([username, email, password]):
        cursor.close()
        conn.close()
        logging.warning("❌ Register: Missing required fields.")
        return jsonify({"status": "error", "message": "All fields are required."}), 400

    # Check if email already exists before attempting insert
    try:
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            conn.close()
            logging.warning(f"❌ Register: Email '{email}' already registered.")
            return jsonify({"status": "error", "message": "Email address is already registered. Please use a different email."}), 409 # 409 Conflict
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logging.error(f"❌ Register: Database error checking for existing email: {err}")
        return jsonify({"status": "error", "message": f"Registration failed: Database error checking email. {str(err)}"}), 500


    hashed_password = generate_password_hash(password)
    logging.info(f"ℹ️ Register: Hashed password generated: '{hashed_password[:20]}...'") # Log a snippet

    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (username, email, hashed_password))
        conn.commit()
        logging.info("✅ Register: User data committed to database.")
        cursor.close()
        conn.close()
        session['registration_success'] = "Registration successful! You can now log in."
        logging.info(f"✅ User '{email}' registered successfully. Redirecting to login page.")
        # For register, still redirect to login page as per previous logic, but ensure frontend handles it
        return redirect(url_for('login_page'))
    except mysql.connector.Error as err: # Catch specific MySQL errors
        conn.rollback()
        cursor.close()
        conn.close()
        logging.error(f"❌ Register error (mysql.connector.Error during insert): {err}")
        return jsonify({"status": "error", "message": f"Registration failed due to database error: {str(err)}"}), 500
    except Exception as e: # Catch any other unexpected errors
        conn.rollback()
        cursor.close()
        conn.close()
        logging.error(f"❌ Register error (General Exception during insert): {e}")
        return jsonify({"status": "error", "message": f"Registration failed due to an unexpected error: {str(e)}"}), 500

# ---------------- LOGIN PAGE ROUTE ----------------
@app.route('/login.html')
def login_page():
    """Renders the login HTML page, handling success/error messages."""
    success_message = session.pop('registration_success', None)
    error_message = request.args.get('error') # Get error message from URL if redirected
    return render_template('login.html', registration_success=success_message, error=error_message)

# ---------------- USER LOGIN ROUTE ----------------
@app.route('/login', methods=['POST'])
def login():
    """Handles user login authentication."""
    # IMPORTANT: Change from request.form to request.json as frontend sends JSON
    data = request.json
    email = data.get('email')
    password = data.get('password')

    logging.debug("ℹ️ User Login: JSON data received: %s", data)
    logging.info(f"ℹ️ User Login: Attempting login for Email: '{email}', Password (length): {len(password) if password else 0}")

    if not all([email, password]):
        logging.warning(f"❌ User Login: Missing email ({email}) or password ({password}).")
        return jsonify({"status": "error", "message": "Email and password are required."}), 400

    conn = get_db_connection()
    if not conn:
        logging.error("❌ User Login: Database connection failed.")
        return jsonify({"status": "error", "message": "Database connection failed. Please try again later."}), 500

    cursor = conn.cursor()
    user = None
    try:
        cursor.execute("SELECT id, email, password, username FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        logging.info(f"ℹ️ User Login: Query executed. User found: {user is not None}")
    except mysql.connector.Error as err:
        logging.error(f"❌ User Login: Database query error: {err}")
        return jsonify({"status": "error", "message": "An error occurred during login."}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    if user:
        user_id, user_email, hashed_password_from_db, username = user
        logging.info(f"ℹ️ User Login: Retrieved user - ID: {user_id}, Email: {user_email}")
        logging.info(f"ℹ️ User Login: Checking password hash for provided password against '{hashed_password_from_db[:20]}...'") # Log a snippet
        if check_password_hash(hashed_password_from_db, password):
            session['user_email'] = user_email
            session['user_id'] = user_id
            session['username'] = username
            logging.info(f"✅ User '{user_email}' logged in successfully. Redirecting to dashboard.")
            # Return JSON for success, frontend will handle redirect
            return jsonify({"status": "success", "redirect": url_for('dashboard')}), 200
        else:
            logging.warning(f"❌ User Login: Invalid password for '{email}'.")
            return jsonify({"status": "error", "message": "Invalid credentials!"}), 401
    else:
        logging.warning(f"❌ User Login: User '{email}' not found.")
        return jsonify({"status": "error", "message": "Invalid credentials!"}), 401

# ---------------- ADMIN LOGIN API ROUTE ----------------
@app.route('/admin_login', methods=['POST'])
def admin_login():
    """Handles admin login authentication."""
    # Assuming admin login also uses JSON submission from frontend
    data = request.json # Changed from request.form to request.json
    email = data.get('email')
    password = data.get('password')

    logging.debug("ℹ️ Admin Login: JSON data received: %s", data)
    logging.info(f"ℹ️ Admin Login: Attempting login for Email: '{email}', Password (length): {len(password) if password else 0}")

    if not email or not password:
        logging.warning(f"❌ Admin Login: Missing email ({email}) or password ({password}).")
        return jsonify({"status": "error", "message": "Email and Password are required!"}), 400

    conn = get_db_connection()
    if not conn:
        logging.error("❌ Admin Login: Database connection failed.")
        return jsonify({"status": "error", "message": "Database connection failed. Please try again later."}), 500

    cursor = conn.cursor(dictionary=True) # Use dictionary=True for easier access by column name
    admin_user = None
    try:
        cursor.execute("SELECT id, email, password FROM admin_users WHERE email = %s", (email,))
        admin_user = cursor.fetchone()
        logging.info(f"ℹ️ Admin Login: Query executed. Admin user found: {admin_user is not None}")
    except mysql.connector.Error as err:
        logging.error(f"❌ Admin Login: Database query error: {err}")
        return jsonify({"status": "error", "message": "An error occurred during admin login."}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    if admin_user:
        logging.info(f"ℹ️ Admin Login: Retrieved admin user - ID: {admin_user['id']}, Email: {admin_user['email']}")
        logging.info(f"ℹ️ Admin Login: Checking password hash for provided password against '{admin_user['password'][:20]}...'") # Log a snippet
        if check_password_hash(admin_user['password'], password):
            session['admin_id'] = admin_user['id']
            session['admin_email'] = admin_user['email']
            session['is_admin'] = True
            logging.info(f"✅ Admin '{email}' logged in successfully. Redirecting to admin dashboard.")
            # Return JSON for success, frontend will handle redirect
            return jsonify({"status": "success", "redirect": url_for('admin_dashboard')}), 200
        else:
            logging.warning(f"❌ Admin Login: Invalid password for admin '{email}'.")
            return jsonify({"status": "error", "message": "Invalid admin credentials!"}), 401
    else:
        logging.warning(f"❌ Admin Login: Admin user '{email}' not found.")
        return jsonify({"status": "error", "message": "Invalid admin credentials!"}), 401

# ---------------- DASHBOARD ROUTE ----------------
@app.route('/dashboard')
def dashboard():
    """Renders the user dashboard, requires user to be logged in."""
    if 'user_id' not in session:
        logging.warning("❌ Dashboard: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    if not conn:
        logging.error("❌ Dashboard: Database connection failed.")
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    user_email = session.get('user_email')
    username = session.get('username', 'User')

    alerts = []
    try:
        cursor.execute("SELECT id, product_name, alert_price FROM price_alerts WHERE user_id = %s", (session['user_id'],))
        alerts = cursor.fetchall()
        logging.info(f"✅ Dashboard: Fetched {len(alerts)} alerts for user {session['user_id']}.")
    except mysql.connector.Error as err:
        logging.error(f"❌ Dashboard: Error fetching alerts: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('dashboard.html', user_email=user_email, username=username, alerts=alerts)

# ---------------- ADMIN DASHBOARD ROUTE ----------------
@app.route('/admin_dashboard')
def admin_dashboard():
    """Renders the admin dashboard, requires admin to be logged in."""
    if 'is_admin' not in session or not session['is_admin']:
        logging.warning("❌ Admin Dashboard: Admin not logged in. Redirecting to admin login.")
        return redirect(url_for('admin_login_page'))

    conn = get_db_connection()
    if not conn:
        logging.error("❌ Admin Dashboard: Database connection failed.")
        return "Database connection failed", 500

    users = []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        logging.info(f"✅ Admin Dashboard: Fetched {len(users)} users.")
    except mysql.connector.Error as err:
        logging.error(f"❌ Admin Dashboard: Database error fetching users: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('admin_dashboard.html', users=users, message=session.pop('message', None), message_type=session.pop('message_type', None))

# ---------------- DELETE USER (ADMIN) ROUTE ----------------
@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    """Handles deletion of a user by an admin."""
    if 'is_admin' not in session or not session['is_admin']:
        logging.warning("❌ Delete User: Admin not logged in. Redirecting to admin login.")
        return redirect(url_for('admin_login_page'))

    conn = get_db_connection()
    if not conn:
        session['message'] = "Database connection failed.";
        session['message_type'] = 'danger';
        logging.error("❌ Delete User: Database connection failed.")
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
        logging.info(f"✅ User ID {user_id} deleted by admin.")
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        session['message'] = f"Error deleting user: {err}";
        session['message_type'] = 'danger';
        logging.error(f"❌ Delete User: Database error deleting user {user_id}: {err}")
    except Exception as e:
        session['message'] = f"An unexpected error occurred: {e}";
        session['message_type'] = 'danger';
        logging.error(f"❌ Delete User: General error deleting user {user_id}: {e}")

    return redirect(url_for('admin_dashboard'))

# ---------------- ALERT SETTINGS PAGE ROUTE ----------------
@app.route('/alert_settings')
def alert_settings_page():
    """Renders the alert settings page, requires user to be logged in."""
    if 'user_id' not in session:
        logging.warning("❌ Alert Settings: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        logging.error("❌ Alert Settings: Database connection failed.")
        return "Database connection failed", 500

    alerts = []
    products = []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, product_name, alert_price FROM price_alerts WHERE user_id = %s", (user_id,))
        alerts = cursor.fetchall()
        logging.info(f"✅ Alert Settings: Fetched {len(alerts)} alerts for user {user_id}.")

        # Fetch products for the dropdown
        products = get_product_list() # Use the helper function
        logging.info(f"✅ Alert Settings: Fetched {len(products)} products for dropdown.")
    except mysql.connector.Error as err:
        logging.error(f"❌ Alert Settings: Error fetching alerts or products: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('alert_settings.html', alerts=alerts, products=products, message=session.pop('alert_message', None))

# ---------------- SET/UPDATE ALERT ROUTE ----------------
@app.route('/set_alert', methods=['POST'])
def set_alert():
    """Handles setting or updating a price alert for a user."""
    if 'user_id' not in session:
        logging.warning("❌ Set Alert: User not logged in. Returning unauthorized.")
        return jsonify({"error": "Unauthorized. Please log in."}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        logging.error("❌ Set Alert: Database connection failed.")
        session['alert_message'] = "Database connection failed."
        return redirect(url_for('alert_settings_page'))

    product = request.form.get('product') # Form uses standard POST, so request.form
    price = request.form.get('price')

    logging.debug(f"ℹ️ Set Alert: Received product: {product}, price: {price}")

    if not product or not price:
        conn.close()
        session['alert_message'] = "Please fill in all fields!"
        logging.warning("❌ Set Alert: Missing product or price.")
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
            logging.info(f"✅ Alert for user {user_id}, product '{product}' updated.")
        else:
            insert_query = "INSERT INTO price_alerts (user_id, product_name, alert_price) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (user_id, product, price))
            conn.commit()
            session['alert_message'] = "Alert set successfully!"
            logging.info(f"✅ Alert for user {user_id}, product '{product}' set.")
        cursor.close()
    except ValueError:
        session['alert_message'] = "Invalid price value. Price must be a number."
        logging.warning("❌ Set Alert: Invalid price value.")
    except mysql.connector.Error as err:
        conn.rollback()
        logging.error(f"❌ Set Alert: Database error setting alert: {err}")
        session['alert_message'] = f"Error setting alert: {err}"
    except Exception as e:
        logging.error(f"❌ Set Alert: General error setting alert: {e}")
        session['alert_message'] = f"An unexpected error occurred: {e}"
    finally:
        if conn and conn.is_connected():
            conn.close()

    return redirect(url_for('alert_settings_page'))

# ---------------- DELETE ALERT ROUTE ----------------
@app.route('/alerts/delete/<int:alert_id>')
def delete_alert(alert_id):
    """Handles deletion of a price alert."""
    if 'user_id' not in session:
        logging.warning("❌ Delete Alert: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        session['alert_message'] = "Database connection failed."
        logging.error("❌ Delete Alert: Database connection failed.")
        return redirect(url_for('alert_settings_page'))

    try:
        cursor = conn.cursor()
        delete_query = "DELETE FROM price_alerts WHERE id = %s AND user_id = %s"
        cursor.execute(delete_query, (alert_id, user_id))
        conn.commit()
        cursor.close()
        session['alert_message'] = "Alert deleted successfully!"
        logging.info(f"✅ Alert ID {alert_id} deleted for user {user_id}.")
    except mysql.connector.Error as err:
        conn.rollback()
        logging.error(f"❌ Delete Alert: Database error deleting alert: {err}")
        session['alert_message'] = f"Error deleting alert: {err}"
    except Exception as e:
        logging.error(f"❌ Delete Alert: General error deleting alert: {e}")
        session['alert_message'] = f"An unexpected error occurred: {e}"
    finally:
        if conn and conn.is_connected():
            conn.close()
    return redirect(url_for('alert_settings_page'))

# ---------------- HISTORICAL PRICE PAGE ROUTE ----------------
@app.route('/historical_price')
def historical_price_page():
    """Renders the historical price trends page, requires user to be logged in."""
    if 'user_id' not in session:
        logging.warning("❌ Historical Price: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    products = get_product_list() # Use the helper function
    return render_template('historical_price.html', products=products)

# ---------------- HISTORICAL PRICE TRENDS API ROUTE ----------------
@app.route('/price_trend', methods=['GET'])
def get_price_trends():
    """Fetches historical price trends for a given product and date range."""
    # This API endpoint does not require user_id in session as it's called via fetch from frontend
    # However, if you want to protect this API, uncomment the session check below:
    # if 'user_id' not in session:
    #     logging.warning("❌ Price Trend API: User not logged in. Returning unauthorized JSON.")
    #     return jsonify({"error": "Unauthorized. Please log in."}), 401

    product = request.args.get('product_name')
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    logging.debug(f"ℹ️ Price Trend API: Received product: {product}, from_date: {from_date_str}, to_date: {to_date_str}")

    if not product or not from_date_str or not to_date_str:
        logging.warning("❌ Price Trend API: Missing product_name, from_date, or to_date.")
        return jsonify({"error": "Please provide product_name, from_date, and to_date."}), 400

    try:
        datetime.strptime(from_date_str, '%Y-%m-%d').date()
        datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        logging.warning("❌ Price Trend API: Invalid date format.")
        return jsonify({"error": "Invalid date format. Use %Y-%m-%d."}), 400

    conn = get_db_connection()
    if not conn:
        logging.error("❌ Price Trend API: Database connection failed.")
        return jsonify({"error": "Database connection failed."}), 500

    cursor = conn.cursor()
    # Ensure product_name comparison is case-insensitive if your data or frontend has mixed case
    # For MySQL, you can use COLLATE utf8mb4_general_ci or LOWER() function
    query = "SELECT date, price FROM historical_prices WHERE product_name=%s AND date BETWEEN %s AND %s ORDER BY date ASC"
    results = []
    try:
        cursor.execute(query, (product, from_date_str, to_date_str))
        db_results = cursor.fetchall()
        logging.debug(f"ℹ️ Price Trend API: Number of results found: {len(db_results)}")
        results = [{"date": row[0].strftime('%Y-%m-%d'), "price": float(row[1])} for row in db_results]
        if not results:
            logging.info("ℹ️ Price Trend API: No data found for the given criteria.")
            return jsonify({"message": "No price data found for the selected product and date range."}), 200
        return jsonify(results)
    except mysql.connector.Error as e:
        logging.error(f"❌ Price Trend API: Database error: {e}")
        return jsonify({"error": f"Error fetching price trends: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------- PRICE PREDICTION PAGE ROUTE ----------------
@app.route('/predict_price')
def predict_price_page():
    """Renders the price prediction page, requires user to be logged in."""
    if 'user_id' not in session:
        logging.warning("❌ Predict Price: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    products = get_product_list() # Use the helper function
    return render_template('predict_price.html', products=products)


# ---------------- PRICE PREDICTION API ROUTE ----------------
@app.route('/predict', methods=['POST'])
def predict():
    """Handles price prediction requests."""
    if 'user_id' not in session:
        logging.warning("❌ Predict API: User not logged in. Returning unauthorized JSON.")
        return jsonify({"error": "Unauthorized. Please log in."}), 401

    if not models:
        logging.warning("❌ Predict API: Prediction models not loaded.")
        return jsonify({"error": "Prediction models are not loaded. Please ensure 'models.pkl' exists and was trained."}), 503

    # Assuming prediction form also uses JSON submission from frontend
    data = request.json # Changed from request.form to request.json
    product = data.get('product')
    date_str = data.get('date')

    logging.debug("ℹ️ Predict API: JSON data received: %s", data)
    logging.info(f"ℹ️ Predict API: Attempting prediction for Product: '{product}', Date: '{date_str}'")

    if not all([product, date_str]):
        logging.warning("❌ Predict API: Missing product or date.")
        return jsonify({"error": "Product and date are required for prediction."}), 400

    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        if input_date < today:
            logging.warning("❌ Predict API: Prediction date in the past.")
            return jsonify({"error": "Enter correct date. Prediction date cannot be in the past."}), 400
    except ValueError:
        logging.warning("❌ Predict API: Invalid date format.")
        return jsonify({"error": "Invalid date format. Use %Y-%m-%d."}), 400

    if product not in models:
        logging.warning(f"❌ Predict API: No model found for product: {product}.")
        return jsonify({"error": f"No prediction model found for product: {product}. Please ensure the model was trained."}), 400

    if df.empty or "Commodities" not in df.columns:
        logging.error("❌ Predict API: Commodity data CSV not loaded properly.")
        return jsonify({"error": "Commodity data CSV not loaded properly."}), 500

    product_data = df[df["Commodities"] == product]
    if product_data.empty:
        logging.warning(f"❌ Predict API: No historical data in CSV for product: {product}.")
        return jsonify({"error": "No historical data found in CSV for this product to make a prediction!"}), 400

    price_columns = [col for col in df.columns if '-' in col and len(col.split('-')[1]) == 2]
    if not price_columns:
        logging.error("❌ Predict API: Not enough price data columns in CSV for prediction.")
        return jsonify({"error": "Not enough price data columns in the CSV for prediction!"}), 400

    latest_price_col = price_columns[-1]

    if latest_price_col not in product_data.columns or pd.isna(product_data[latest_price_col].iloc[0]):
        logging.warning(f"❌ Predict API: Latest price data not available in CSV for {product}.")
        return jsonify({"error": f"Latest price data not available in CSV for {product} to make a prediction."}), 400

    latest_price = product_data[latest_price_col].iloc[0]
    prediction_input = [[latest_price]]

    conn = None # Initialize conn to None for finally block
    try:
        model = models[product]
        predicted_price = model.predict(prediction_input)[0]
        predicted_price_mysql = float(round(predicted_price, 2))
        logging.info(f"✅ Predict API: Predicted price for {product} on {date_str}: {predicted_price_mysql}")

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "INSERT INTO price_predictions (product_name, predicted_price, prediction_date) VALUES (%s, %s, %s)"
            cursor.execute(query, (product, predicted_price_mysql, date_str))
            conn.commit()
            cursor.close()
            logging.info("✅ Predict API: Prediction saved to database.")
            return jsonify({"predicted_price": predicted_price_mysql})
        else:
            logging.warning("⚠ Predict API: Could not save prediction to database (DB connection failed).")
            return jsonify({"predicted_price": predicted_price_mysql, "warning": "Could not save prediction to database."}), 200

    except Exception as e:
        logging.error(f"❌ Predict API: Error during prediction or DB save: {e}")
        if conn and conn.is_connected():
            conn.rollback() # Rollback if error occurred after connection
            conn.close()
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500
    finally:
        # Ensure connection is closed even if not explicitly handled in try/except
        if conn and conn.is_connected():
            conn.close()


# ---------------- LOGOUT ROUTE ----------------
@app.route('/logout')
def logout():
    """Logs out the current user by clearing session and redirects to logged out page."""
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('username', None) # Clear username from session
    session.pop('admin_id', None) # Clear admin session if exists
    session.pop('admin_email', None)
    session.pop('is_admin', None)
    logging.info("✅ User logged out. Clearing session.")
    return redirect(url_for('loggedout_page'))

# ---------------- LOGGED OUT PAGE ROUTE ----------------
@app.route('/loggedout.html')
def loggedout_page():
    """Renders the logged out confirmation page."""
    return render_template('loggedout.html')

# ---------------- RUN THE FLASK APPLICATION ----------------
if __name__ == "__main__":
    logging.info("✅ Starting Flask app...")
    # Render sets the PORT environment variable. Use it if available.
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
