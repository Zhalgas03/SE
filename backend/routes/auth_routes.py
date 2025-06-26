from flask import Blueprint, request, jsonify, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from db import get_db_connection
from config import Config
from requests_oauthlib import OAuth2Session
import re
import time

auth_routes = Blueprint("auth", __name__, url_prefix="/api")

@auth_routes.route("/auth/google")
def google_login():
    google = OAuth2Session(Config.GOOGLE_CLIENT_ID, redirect_uri=Config.REDIRECT_URI, scope=["openid", "email", "profile"])
    auth_url, state = google.authorization_url("https://accounts.google.com/o/oauth2/auth", access_type="offline")
    session["oauth_state"] = state
    return redirect(auth_url)

@auth_routes.route("/auth/google/callback")
def google_callback():
    google = OAuth2Session(Config.GOOGLE_CLIENT_ID, state=session["oauth_state"], redirect_uri=Config.REDIRECT_URI)
    token = google.fetch_token("https://oauth2.googleapis.com/token",
                               client_secret=Config.GOOGLE_CLIENT_SECRET,
                               authorization_response=request.url)
    user_info = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
    email = user_info["email"]
    name = user_info.get("name", "GoogleUser")

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            if not user:
                cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                            (name, email, generate_password_hash("google_dummy")))
                conn.commit()
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cur.fetchone()

        token = None
        if user is not None:
            token = create_access_token(identity={'username': user['username'], 'email': user['email']})
            return redirect(f"http://localhost:3000?token={token}&username={user['username']}")
        else:
            return jsonify(success=False, message="User not found after registration"), 500

    except Exception as e:
        print("Google OAuth error:", str(e))
        return jsonify(success=False, message="OAuth error"), 500

@auth_routes.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password")

    if not all([username, email, password]):
        return jsonify(success=False, message="All fields are required."), 400

    if not re.search(r'[a-zA-Z]', username):
        return jsonify(success=False, message="Username must contain letters"), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify(success=False, message="Invalid email format"), 400

    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
        return jsonify(success=False, message="Weak password"), 400

    hashed = generate_password_hash(password)

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, email))
                if cur.fetchone():
                    return jsonify(success=False, message="Username or email exists."), 409

                cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                            (username, email, hashed))

        token = create_access_token(identity={"username": username, "email": email})
        return jsonify(success=True, token=token, username=username)

    except Exception as e:
        print("❌ Register error:", str(e))
        return jsonify(success=False, message="Server error"), 500

@auth_routes.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not all([email, password]):
        return jsonify(success=False, message="Email and password required"), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            if user is not None and check_password_hash(user["password_hash"], password):
                token = create_access_token(identity={"username": user["username"], "email": user["email"]})
                return jsonify(success=True, token=token, username=user["username"])
            else:
                return jsonify(success=False, message="Invalid credentials"), 401

    except Exception as e:
        print("Login error:", str(e))
        return jsonify(success=False, message="Server error"), 500

@auth_routes.route('/user/profile', methods=['GET'])
def user_profile():
    # Dummy implementation for testing
    return jsonify({"username": "test", "email": "test@example.com"}), 200
