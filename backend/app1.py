from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
import re  # <-- ДОБАВЬ СЮДА!
import pymysql
from dotenv import load_dotenv
import os
import requests
from flask import redirect, session, url_for
from requests_oauthlib import OAuth2Session
load_dotenv()
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:5000/api/auth/google/callback"
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

@app.route("/api/auth/google")
def google_login():
    google = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=REDIRECT_URI, scope=["openid", "email", "profile"])
    auth_url, state = google.authorization_url(AUTHORIZATION_BASE_URL, access_type="offline")
    session["oauth_state"] = state
    return redirect(auth_url)

@app.route("/api/auth/google/callback")
def google_callback():
    google = OAuth2Session(GOOGLE_CLIENT_ID, state=session["oauth_state"], redirect_uri=REDIRECT_URI)
    token = google.fetch_token(TOKEN_URL, client_secret=GOOGLE_CLIENT_SECRET, authorization_response=request.url)
    resp = google.get(USER_INFO_URL)
    user_info = resp.json()

    email = user_info["email"]
    name = user_info.get("name", "GoogleUser")

    # Поиск в БД
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    if not user:
        # Автоматическая регистрация
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (name, email, generate_password_hash("google_dummy")))
        mysql.connection.commit()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

    cur.close()

    access_token = create_access_token(identity={'username': user[1], 'email': user[2]})
    return redirect(f"http://localhost:3000?token={access_token}&username={user[1]}")



from flask import request, jsonify
import requests
import os

chat_history = []

SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are a smart and focused travel planner assistant.

Ask the user exactly 6 questions, one at a time, in this order:

1. Where would you like to go?
2. When are you planning to travel?
3. What do you want to do there? (e.g. business, sightseeing, food, walking)
4. What is your travel style? (e.g. budget, relaxed, adventurous)
5. What is your budget?
6. Are you traveling solo or with others?

✅ Do not confirm, rephrase, or summarize the user's answers after each response.  
✅ Just move on to the next question.  
✅ Be minimal and direct.

If the user gives a vague answer like a country, region, or "somewhere warm", ask them to specify a **city**. You can suggest 2–3 cities by name only (no descriptions).

If the user asks for recommendations before the questionnaire is complete, suggest a few cities **without any extra info**, then continue to the next question.

❗Only after all 6 answers are collected, briefly summarize the trip details in bullet points.  
Then, and only then, generate a personalized travel plan with accommodation, POIs, and practical suggestions.

Do not generate long responses unless the user explicitly asks for details.
"""
}



@app.route('/api/perplexity-chat', methods=['POST'])
def perplexity_chat():
    global chat_history
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'reply': 'No input received.'}), 400

    if not chat_history:
        chat_history = [SYSTEM_PROMPT]

    chat_history.append({"role": "user", "content": user_message})

    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY is missing.")
        return jsonify({'reply': 'Missing API key.'}), 500

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        body = {
            "model": "sonar",  # ✅ единственная допустимая строка
            "messages": chat_history
        }

        res = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=body)

        print("Perplexity status code:", res.status_code)
        print("Perplexity response:", res.text)

        if res.status_code == 200:
            reply = res.json()["choices"][0]["message"]["content"]
            chat_history.append({"role": "assistant", "content": reply})
            return jsonify({'reply': reply})
        else:
            return jsonify({'reply': 'Perplexity API error'}), 500

    except Exception as e:
        print("❌ Exception:", e)
        return jsonify({'reply': 'Server error'}), 500



# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'tripuser'
app.config['MYSQL_PASSWORD'] = 'trippass'
app.config['MYSQL_DB'] = 'tripdb'

# JWT config
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

mysql = MySQL(app)
jwt = JWTManager(app)

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

    # Проверка на пустые поля
    if not all([username, email, password]):
        return jsonify(success=False, message="All fields are required."), 400

    # ✅ Проверка: username должен содержать хотя бы одну букву (латиница)
    if not re.search(r'[a-zA-Z]', username):
        return jsonify(success=False, message="Username must contain at least one letter."), 400

    # Email валидация
    try:
        validate_email(email)
    except EmailNotValidError:
        return jsonify(success=False, message="Invalid email address."), 400

    # Проверка пароля по стандарту
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
