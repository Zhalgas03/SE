from flask import Flask, request, jsonify, redirect, session, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from requests_oauthlib import OAuth2Session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import re
import requests
from dotenv import load_dotenv
import time
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:5000/api/auth/google/callback"
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

app.config['JWT_SECRET_KEY'] = 'super-secret-key'
jwt = JWTManager(app)

def get_db_connection():
    return psycopg2.connect(
        host="gondola.proxy.rlwy.net",
        port=15216,
        database="railway",
        user="postgres",
        password="NxWQAwqlQgIzNdNUiuPEHEHtnTjBQBlY",
        cursor_factory=RealDictCursor
    )

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

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            if not user:
                cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                            (name, email, generate_password_hash("google_dummy")))
                conn.commit()
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cur.fetchone()

        access_token = create_access_token(identity={'username': user['username'], 'email': user['email']})
        return redirect(f"http://localhost:3000?token={access_token}&username={user['username']}")

    except Exception as e:
        print("Google OAuth error:", str(e))
        return jsonify(success=False, message="OAuth error"), 500


@app.route('/api/register', methods=['POST'])
def register():
    start_time = time.time()  # 🕒 начало замера

    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify(success=False, message="All fields are required."), 400

    # Простейшая проверка username и email
    if not re.search(r'[a-zA-Z]', username):
        return jsonify(success=False, message="Username must contain at least one letter."), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify(success=False, message="Invalid email format."), 400

    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
        return jsonify(success=False, message="Password must be at least 8 characters and include uppercase, lowercase letters and a number."), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        with conn:  # автоматический commit
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, email))
                if cur.fetchone():
                    return jsonify(success=False, message="Username or email already exists."), 409

                cur.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password)
                )

        access_token = create_access_token(identity={'username': username, 'email': email})

        print("✅ Register completed in", round(time.time() - start_time, 2), "seconds")  # ⏱️ замер времени
        return jsonify(success=True, token=access_token, username=username), 200

    except Exception as e:
        print("❌ Register error:", str(e))
        return jsonify(success=False, message="Unexpected server error"), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password_input = data.get('password', '')

    if not all([email, password_input]):
        return jsonify(success=False, message="Email and password are required."), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            if user and check_password_hash(user['password'], password_input):
                access_token = create_access_token(identity={
                    'username': user['username'],
                    'email': user['email']
                })
                return jsonify(success=True, token=access_token, username=user['username']), 200
            else:
                return jsonify(success=False, message="Invalid email or password"), 401

    except Exception as e:
        print("Login error:", str(e))
        return jsonify(success=False, message="Server error"), 500


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
            "model": "sonar",
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


@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask!")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
