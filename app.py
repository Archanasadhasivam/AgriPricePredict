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
# IMPORTANT: Replace "your_very_secret_and_long_random_key_here" with a strong, random key
# For production, set this as an environment variable in Render.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_very_secure_and_long_random_string_for_flask_session_keys_1234567890")

# ✅ Database connection details from environment variables
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
        print("✅ Database connection established.")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
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
df = pd.DataFrame() # Initialize as empty DataFrame
try:
    df = pd.read_csv("commodity_price.csv")
    df.columns = df.columns.str.strip() # Clean column names
    if "Commodities" in df.columns:
        print("✅ Products loaded from CSV:", df["Commodities"].unique())
    else:
        print("❌ 'Commodities' column not found in 'commodity_price.csv'. Please check the CSV structure.")
        df = pd.DataFrame() # Ensure df is empty if column is missing
except FileNotFoundError:
    print("❌ Error: 'commodity_price.csv' not found.")
except Exception as e:
    print(f"❌ Error loading commodity data from CSV: {e}")
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
        print("❌ Register: Database connection failed.")
        return redirect(url_for('signup_page', error="Database connection failed. Please try again later."))

    cursor = conn.cursor()
    data = request.form # Data from HTML form submission
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        cursor.close()
        conn.close()
        print("❌ Register: Missing required fields.")
        return redirect(url_for('signup_page', error="All fields are required."))

    hashed_password = generate_password_hash(password)

    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    try:
        cursor.execute(query, (username, email, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        session['registration_success'] = "Registration successful! You can now log in."
        print(f"✅ User '{email}' registered successfully.")
        return redirect(url_for('login_page'))
    except mysql.connector.IntegrityError as err:
        conn.rollback()
        cursor.close()
        conn.close()
        if "Duplicate entry" in str(err) and "email" in str(err):
            print(f"❌ Register: Email '{email}' already registered.")
            return redirect(url_for('signup_page', error="Email address is already registered."))
        else:
            print(f"❌ Register error (IntegrityError): {err}")
            return redirect(url_for('signup_page', error=f"Registration failed: {str(err)}"))
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        print(f"❌ Register error (General Exception): {e}")
        return redirect(url_for('signup_page', error=f"Registration failed: {str(e)}"))

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
    conn = get_db_connection()
    if not conn:
        print("❌ User Login: Database connection failed.")
        return redirect(url_for('login_page', error="Database connection failed. Please try again later."))

    cursor = conn.cursor()
    data = request.form # Data from HTML form submission
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        cursor.close()
        conn.close()
        print("❌ User Login: Missing email or password.")
        return redirect(url_for('login_page', error="Email and password are required."))

    user = None
    try:
        cursor.execute("SELECT id, email, password, username FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        print(f"ℹ️ User Login: Query executed. User found: {user is not None}")
    except mysql.connector.Error as err:
        print(f"❌ User Login: Database query error: {err}")
        cursor.close()
        conn.close()
        return redirect(url_for('login_page', error="An error occurred during login."))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    if user:
        user_id, user_email, hashed_password_from_db, username = user
        print(f"ℹ️ User Login: Retrieved user - ID: {user_id}, Email: {user_email}")
        print(f"ℹ️ User Login: Checking password hash for provided password against '{hashed_password_from_db[:20]}...'") # Log a snippet of the hash
        if check_password_hash(hashed_password_from_db, password):
            session['user_email'] = user_email
            session['user_id'] = user_id
            session['username'] = username
            print(f"✅ User '{user_email}' logged in successfully. Redirecting to dashboard.")
            return redirect(url_for('dashboard'))
        else:
            print(f"❌ User Login: Invalid password for '{email}'.")
            return redirect(url_for('login_page', error="Invalid credentials!"))
    else:
        print(f"❌ User Login: User '{email}' not found.")
        return redirect(url_for('login_page', error="Invalid credentials!"))

# ---------------- ADMIN LOGIN API ROUTE ----------------
@app.route('/admin_login', methods=['POST'])
def admin_login():
    """Handles admin login authentication."""
    conn = get_db_connection()
    if not conn:
        print("❌ Admin Login: Database connection failed.")
        return redirect(url_for('admin_login_page', error='Database connection failed. Please try again later.'))

    cursor = conn.cursor(dictionary=True) # Use dictionary=True for easier access by column name
    data = request.form # Data from HTML form submission
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        cursor.close()
        conn.close()
        print("❌ Admin Login: Missing email or password.")
        return redirect(url_for('admin_login_page', error='Email and Password are required!'))

    admin_user = None
    try:
        cursor.execute("SELECT id, email, password FROM admin_users WHERE email = %s", (email,))
        admin_user = cursor.fetchone()
        print(f"ℹ️ Admin Login: Query executed. Admin user found: {admin_user is not None}")
    except mysql.connector.Error as err:
        print(f"❌ Admin Login: Database query error: {err}")
        cursor.close()
        conn.close()
        return redirect(url_for('admin_login_page', error="An error occurred during admin login."))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    if admin_user:
        print(f"ℹ️ Admin Login: Retrieved admin user - ID: {admin_user['id']}, Email: {admin_user['email']}")
        print(f"ℹ️ Admin Login: Checking password hash for provided password against '{admin_user['password'][:20]}...'") # Log a snippet
        if check_password_hash(admin_user['password'], password):
            session['admin_id'] = admin_user['id']
            session['admin_email'] = admin_user['email']
            session['is_admin'] = True
            print(f"✅ Admin '{email}' logged in successfully. Redirecting to admin dashboard.")
            return redirect(url_for('admin_dashboard'))
        else:
            print(f"❌ Admin Login: Invalid password for admin '{email}'.")
            return redirect(url_for('admin_login_page', error='Invalid admin credentials!'))
    else:
        print(f"❌ Admin Login: Admin user '{email}' not found.")
        return redirect(url_for('admin_login_page', error='Invalid admin credentials!'))

# ---------------- DASHBOARD ROUTE ----------------
@app.route('/dashboard')
def dashboard():
    """Renders the user dashboard, requires user to be logged in."""
    if 'user_id' not in session:
        print("❌ Dashboard: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    if not conn:
        print("❌ Dashboard: Database connection failed.")
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    user_email = session.get('user_email')
    username = session.get('username', 'User')

    alerts = []
    try:
        cursor.execute("SELECT id, product_name, alert_price FROM price_alerts WHERE user_id = %s", (session['user_id'],))
        alerts = cursor.fetchall()
        print(f"✅ Dashboard: Fetched {len(alerts)} alerts for user {session['user_id']}.")
    except mysql.connector.Error as err:
        print(f"❌ Dashboard: Error fetching alerts: {err}")
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
        print("❌ Admin Dashboard: Admin not logged in. Redirecting to admin login.")
        return redirect(url_for('admin_login_page'))

    conn = get_db_connection()
    if not conn:
        print("❌ Admin Dashboard: Database connection failed.")
        return "Database connection failed", 500

    users = []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        print(f"✅ Admin Dashboard: Fetched {len(users)} users.")
    except mysql.connector.Error as err:
        print(f"❌ Admin Dashboard: Database error fetching users: {err}")
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
        print("❌ Delete User: Admin not logged in. Redirecting to admin login.")
        return redirect(url_for('admin_login_page'))

    conn = get_db_connection()
    if not conn:
        session['message'] = "Database connection failed.";
        session['message_type'] = 'danger';
        print("❌ Delete User: Database connection failed.")
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
        print(f"✅ User ID {user_id} deleted by admin.")
    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        conn.close()
        session['message'] = f"Error deleting user: {err}";
        session['message_type'] = 'danger';
        print(f"❌ Delete User: Database error deleting user {user_id}: {err}")
    except Exception as e:
        session['message'] = f"An unexpected error occurred: {e}";
        session['message_type'] = 'danger';
        print(f"❌ Delete User: General error deleting user {user_id}: {e}")

    return redirect(url_for('admin_dashboard'))

# ---------------- ALERT SETTINGS PAGE ROUTE ----------------
@app.route('/alert_settings')
def alert_settings_page():
    """Renders the alert settings page, requires user to be logged in."""
    if 'user_id' not in session:
        print("❌ Alert Settings: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        print("❌ Alert Settings: Database connection failed.")
        return "Database connection failed", 500

    alerts = []
    products = []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, product_name, alert_price FROM price_alerts WHERE user_id = %s", (user_id,))
        alerts = cursor.fetchall()
        print(f"✅ Alert Settings: Fetched {len(alerts)} alerts for user {user_id}.")

        cursor.execute("SELECT DISTINCT product_name FROM historical_prices ORDER BY product_name ASC")
        product_results = cursor.fetchall()
        products = [row['product_name'] for row in product_results]
        print(f"✅ Alert Settings: Fetched {len(products)} products for dropdown.")
    except mysql.connector.Error as err:
        print(f"❌ Alert Settings: Error fetching alerts or products: {err}")
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
        print("❌ Set Alert: User not logged in. Returning unauthorized.")
        return jsonify({"error": "Unauthorized. Please log in."}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        print("❌ Set Alert: Database connection failed.")
        session['alert_message'] = "Database connection failed."
        return redirect(url_for('alert_settings_page'))

    product = request.form.get('product')
    price = request.form.get('price')

    if not product or not price:
        conn.close()
        session['alert_message'] = "Please fill in all fields!"
        print("❌ Set Alert: Missing product or price.")
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
            print(f"✅ Alert for user {user_id}, product '{product}' updated.")
        else:
            insert_query = "INSERT INTO price_alerts (user_id, product_name, alert_price) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (user_id, product, price))
            conn.commit()
            session['alert_message'] = "Alert set successfully!"
            print(f"✅ Alert for user {user_id}, product '{product}' set.")
        cursor.close()
    except ValueError:
        session['alert_message'] = "Invalid price value."
        print("❌ Set Alert: Invalid price value.")
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"❌ Set Alert: Database error setting alert: {err}")
        session['alert_message'] = f"Error setting alert: {err}"
    except Exception as e:
        print(f"❌ Set Alert: General error setting alert: {e}")
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
        print("❌ Delete Alert: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        session['alert_message'] = "Database connection failed."
        print("❌ Delete Alert: Database connection failed.")
        return redirect(url_for('alert_settings_page'))

    try:
        cursor = conn.cursor()
        delete_query = "DELETE FROM price_alerts WHERE id = %s AND user_id = %s"
        cursor.execute(delete_query, (alert_id, user_id))
        conn.commit()
        cursor.close()
        session['alert_message'] = "Alert deleted successfully!"
        print(f"✅ Alert ID {alert_id} deleted for user {user_id}.")
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"❌ Delete Alert: Database error deleting alert: {err}")
        session['alert_message'] = f"Error deleting alert: {err}"
    except Exception as e:
        print(f"❌ Delete Alert: General error deleting alert: {e}")
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
        print("❌ Historical Price: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    if not conn:
        print("❌ Historical Price: Database connection failed.")
        return "Database connection failed", 500

    products = []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT product_name FROM historical_prices ORDER BY product_name ASC")
        product_results = cursor.fetchall()
        products = [row['product_name'] for row in product_results]
        print(f"✅ Historical Price: Fetched {len(products)} products for dropdown.")
    except mysql.connector.Error as err:
        print(f"❌ Historical Price: Database error fetching products: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('historical_price.html', products=products)

# ---------------- PRICE PREDICTION PAGE ROUTE ----------------
@app.route('/predict_price')
def predict_price_page():
    """Renders the price prediction page, requires user to be logged in."""
    if 'user_id' not in session:
        print("❌ Predict Price: User not logged in. Redirecting to login.")
        return redirect(url_for('login_page'))

    conn = get_db_connection()
    if not conn:
        print("❌ Predict Price: Database connection failed.")
        return "Database connection failed", 500

    products = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT product_name FROM historical_prices ORDER BY product_name ASC")
        product_results = cursor.fetchall()
        products = [row[0] for row in product_results]
        print(f"✅ Predict Price: Fetched {len(products)} products for dropdown.")
    except mysql.connector.Error as err:
        print(f"❌ Predict Price: Database error fetching products: {err}")
    finally:
        if conn and conn.is_connected():
            conn.close()
    return render_template('predict_price.html', products=products)


# ---------------- PRICE PREDICTION API ROUTE ----------------
@app.route('/predict', methods=['POST'])
def predict():
    """Handles price prediction requests."""
    if 'user_id' not in session:
        print("❌ Predict API: User not logged in. Returning unauthorized JSON.")
        return jsonify({"error": "Unauthorized. Please log in."}), 401

    if not models:
        print("❌ Predict API: Prediction models not loaded.")
        return jsonify({"error": "Prediction models are not loaded. Please ensure 'models.pkl' exists and was trained."}), 503

    data = request.form # Data from HTML form submission
    product = data.get('product')
    date_str = data.get('date')

    if not all([product, date_str]):
        print("❌ Predict API: Missing product or date.")
        return jsonify({"error": "Product and date are required for prediction."}), 400

    try:
        input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        if input_date < today:
            print("❌ Predict API: Prediction date in the past.")
            return jsonify({"error": "Enter correct date. Prediction date cannot be in the past."}), 400
    except ValueError:
        print("❌ Predict API: Invalid date format.")
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if product not in models:
        print(f"❌ Predict API: No model found for product: {product}.")
        return jsonify({"error": f"No prediction model found for product: {product}. Please ensure the model was trained."}), 400

    if df.empty or "Commodities" not in df.columns:
        print("❌ Predict API: Commodity data CSV not loaded properly.")
        return jsonify({"error": "Commodity data CSV not loaded properly."}), 500

    product_data = df[df["Commodities"] == product]
    if product_data.empty:
        print(f"❌ Predict API: No historical data in CSV for product: {product}.")
        return jsonify({"error": "No historical data found in CSV for this product to make a prediction!"}), 400

    price_columns = [col for col in df.columns if '-' in col and len(col.split('-')[1]) == 2]
    if not price_columns:
        print("❌ Predict API: Not enough price data columns in CSV for prediction.")
        return jsonify({"error": "Not enough price data columns in the CSV for prediction!"}), 400

    latest_price_col = price_columns[-1]

    if latest_price_col not in product_data.columns or pd.isna(product_data[latest_price_col].iloc[0]):
        print(f"❌ Predict API: Latest price data not available in CSV for {product}.")
        return jsonify({"error": f"Latest price data not available in CSV for {product} to make a prediction."}), 400

    latest_price = product_data[latest_price_col].iloc[0]
    prediction_input = [[latest_price]]

    conn = None # Initialize conn to None for finally block
    try:
        model = models[product]
        predicted_price = model.predict(prediction_input)[0]
        predicted_price_mysql = float(round(predicted_price, 2))
        print(f"✅ Predict API: Predicted price for {product} on {date_str}: {predicted_price_mysql}")

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "INSERT INTO price_predictions (product_name, predicted_price, prediction_date) VALUES (%s, %s, %s)"
            cursor.execute(query, (product, predicted_price_mysql, date_str))
            conn.commit()
            cursor.close()
            print("✅ Predict API: Prediction saved to database.")
            return jsonify({"predicted_price": predicted_price_mysql})
        else:
            print("⚠ Predict API: Could not save prediction to database (DB connection failed).")
            return jsonify({"predicted_price": predicted_price_mysql, "warning": "Could not save prediction to database."}), 200

    except Exception as e:
        print(f"❌ Predict API: Error during prediction or DB save: {e}")
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
    print("✅ User logged out. Clearing session.")
    return redirect(url_for('loggedout_page'))

# ---------------- LOGGED OUT PAGE ROUTE ----------------
@app.route('/loggedout.html')
def loggedout_page():
    """Renders the logged out confirmation page."""
    return render_template('loggedout.html')

# ---------------- RUN THE FLASK APPLICATION ----------------
if __name__ == "__main__":
    print("✅ Starting Flask app...")
    # Render sets the PORT environment variable. Use it if available.
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
