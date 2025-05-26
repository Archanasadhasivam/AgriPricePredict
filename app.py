from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
import bcrypt

app = Flask(__name__)
CORS(app)

# Secret key for session management
app.secret_key = 'your_secret_key_here'

# MySQL database connection config
db = mysql.connector.connect(
    host="localhost",
    user="your_db_user",
    password="your_db_password",
    database="your_db_name"
)
cursor = db.cursor()

# Home route - renders login page
@app.route('/')
def home():
    return render_template('login.html')

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    query = "SELECT id, password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        session['user_id'] = user[0]
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'error': 'Invalid username or password'}), 401

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return f"<h1>Welcome User {session['user_id']}</h1><br><a href='/logout'>Logout</a>"
    else:
        return redirect(url_for('home'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Signup page
@app.route('/signup')
def signup_route():
    return "<h1>Sign Up Page</h1>"

# Admin login page
@app.route('/admin_login')
def admin_login_route():
    return "<h1>Admin Login Page</h1>"

if __name__ == '__main__':
    app.run(debug=True)
