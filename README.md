A web application designed for agricultural price prediction. It appears to involve machine learning models and data management for commodity pricing.
Tech Stack
Python: Core application logic and likely machine learning (.py, .pkl files, requirements.txt).
PHP: Database interaction (db.php, logout.php).
HTML/CSS: Frontend templating (template, templates directories).
SQL: Database schema and data insertion (database.sql, insert_queries.sql, sql_insert_code.py).
Core Functionality
Price prediction (implied by model.pkl, models.pkl, and project name).
Data storage and retrieval (via .db.php, .sql files).
User interface for interaction (via template, templates directories).
Common User authentication (implied by login.php and logout.php).
Setup and Installation
Prerequisites
Python (implied by .py files and requirements.txt).
PHP (implied by .php files).
A database system (implied by .sql files).
Clone the repository
cd AgriPricePredict
Install Python Dependencies:pip install -r requirements.txt
Database Configuration:
Set up your database based on database.sql.
Execute insert_queries.sql and sql_insert_code.py to populate initial data.
Configure database connection details within the relevant PHP and Python files (e.g., db.php, db_connect.py).
Application Execution:
The application involves running Python scripts (app.py) and PHP files (db.php, login.php, logout.php). Specific execution commands would depend on your server setup (e.g., how you run Python web applications and serve PHP files).
