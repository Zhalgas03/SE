from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
import re
import pymysql
import os

# Поддержка PyMySQL (если используешь вместо mysqlclient)
pymysql.install_as_MySQLdb()

# Указываем, что статика (frontend) лежит в папке build
app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'tripuser'
app.config['MYSQL_PASSWORD'] = 'trippass'
app.config['MYSQL_DB'] = 'tripdb'

# JWT config
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

mysql = MySQL(app)
jwt = JWTManager(app)

# Serve React frontend
@app.route('/')
def serve_react():
    return send_from_directory(app.static_folder, 'index.html')

# Handle React routes (e.g., /login, /dashboard) by always returning index.html
@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')

# API Endpoints
@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask!")

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not all([username, email, password]):
        return jsonify(success=False, message="All fields are required."), 400

    if not re.search(r'[a-zA-Z]', username):
        return jsonify(success=False, message="Username must contain at least one letter."), 400

    try:
        validate_email(email)
    except EmailNotValidError:
        return jsonify(success=False, message="Invalid email address."), 400

    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
        return jsonify(success=False, message="Password must be at least 8 characters and include uppercase, lowercase letters and a number."), 400

    hashed_password = generate_password_hash(password)

    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password))
        mysql.connection.commit()
        cur.close()
        return jsonify(success=True, message="User registered successfully."), 201

    except Exception as e:
        error_msg = str(e)
        if "Duplicate entry" in error_msg and "username" in error_msg:
            return jsonify(success=False, message="This username is already taken. Please choose another."), 409
        elif "Duplicate entry" in error_msg and "email" in error_msg:
            return jsonify(success=False, message="This email is already registered. Please use another."), 409
        else:
            print("Unexpected error:", error_msg)
            return jsonify(success=False, message="Unexpected server error"), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password_input = data.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[3], password_input):
        access_token = create_access_token(identity={'username': user[1], 'email': user[2]})
        return jsonify(success=True, token=access_token, username=user[1]), 200
    else:
        return jsonify(success=False, message="Invalid email or password"), 401

if __name__ == "__main__":
    app.run(port=5000, debug=True)
