from flask import Blueprint, request, jsonify, redirect, session
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from services.oauth_service import get_google_auth, get_user_info
from config import Config
import re

auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify(success=False, message="All fields are required."), 400

    if not re.search(r'[a-zA-Z]', username):
        return jsonify(success=False, message="Username must contain at least one letter."), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify(success=False, message="Invalid email format."), 400

    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
        return jsonify(success=False, message="Password must be at least 8 characters and include uppercase, lowercase letters and a number."), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, email))
                if cur.fetchone():
                    return jsonify(success=False, message="Username or email already exists."), 409

                cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, hashed_password)
                )
        access_token = create_access_token(identity=username)
        return jsonify(success=True, token=access_token, username=username), 200
    except Exception as e:
        print("❌ Register error:", str(e))
        return jsonify(success=False, message="Unexpected server error"), 500

@auth_bp.route("/login", methods=["POST"])
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
            if user and check_password_hash(user['password_hash'], password_input):
                username = user['username']
                access_token = create_access_token(identity=username)
                return jsonify(success=True, token=access_token, username=user['username']), 200
            else:
                return jsonify(success=False, message="Invalid email or password"), 401
    except Exception as e:
        print("Login error:", str(e))
        return jsonify(success=False, message="Server error"), 500

# GOOGLE OAUTH HANDLERS
@auth_bp.route("/auth/google")
def google_login():
    google = get_google_auth()
    auth_url, state = google.authorization_url(Config.AUTHORIZATION_BASE_URL, access_type="offline")
    session["oauth_state"] = state
    return redirect(auth_url)

@auth_bp.route("/auth/google/callback")
def google_callback():
    try:
        user_info = get_user_info(request.url)
        email = user_info["email"]
        name = user_info.get("name", "GoogleUser")
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
        access_token = create_access_token(identity={'username': user['username'], 'email': user['email']})
        return redirect(f"http://localhost:3000?token={access_token}&username={user['username']}")
    except Exception as e:
        print("Google OAuth error:", str(e))
        return jsonify(success=False, message="OAuth error"), 500
