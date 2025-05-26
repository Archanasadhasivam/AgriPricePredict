# your_db_file.py (or whatever name you chose)
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', 3306)
DB_SSL_CA = os.getenv('DB_SSL_CA')

def get_db_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            ssl_mode='REQUIRED',
            ssl_ca=DB_SSL_CA
        )
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
    return conn

if __name__ == '__main__':
    db_connection = get_db_connection()
    if db_connection:
        print("Successfully connected to the database!")
        db_connection.close()
    else:
        print("Failed to connect to the database.")

