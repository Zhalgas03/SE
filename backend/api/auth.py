from flask import Blueprint, request, jsonify, redirect, session
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from services.oauth_service import get_google_auth, get_user_info
from config import Config
import re
from psycopg2.extras import RealDictCursor
from typing import Any, Dict
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os
from models.email_2fa import generate_2fa_code, send_2fa_email
from datetime import datetime, timedelta, timezone
from flask_dance.contrib.github import make_github_blueprint, github   
from flask import redirect, url_for, jsonify


auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user = get_jwt_identity()
    return jsonify(success=True, username=user), 200



@auth_bp.route("/register", methods=["POST"])
def register():
    
    # Verify captcha
    def verify_captcha(token: str) -> bool:
        secret = Config.RECAPTCHA_SECRET_KEY
        payload = {
            'secret': secret,
            'response': token
        }
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
        result = response.json()
        return result.get("success", False)
    
    # Get data from request
    data = request.get_json()
    captcha_token = data.get('captchaToken')
    if not captcha_token or not verify_captcha(captcha_token):
        return jsonify(success=False, message="Captcha verification failed."), 400

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
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (username, email))
            if cur.fetchone():
                return jsonify(success=False, message="Username or email already exists."), 409

            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            conn.commit()

        access_token = create_access_token(identity=username)
        return jsonify(success=True, token=access_token, username=username), 200
    except Exception as e:
        print("❌ Register error:", str(e))
        return jsonify(success=False, message="Unexpected server error"), 500


@auth_bp.route("/login", methods=["POST"])
def login():

    # Verify captcha
    def verify_captcha(token: str) -> bool:
        secret = Config.RECAPTCHA_SECRET_KEY
        payload = {
            'secret': secret,
            'response': token
        }
        response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
        result = response.json()
        return result.get("success", False)

    # Get data from request
    data = request.get_json()
    email = data.get('email', '').strip()
    password_input = data.get('password', '')

    captcha_token = data.get('captchaToken')
    if not captcha_token or not verify_captcha(captcha_token):
        return jsonify(success=False, message="CAPTCHA verification failed"), 400

    if not all([email, password_input]):
        return jsonify(success=False, message="Email and password are required."), 400

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user and check_password_hash(user['password_hash'], password_input):
                username = user['username']
                is_2fa_enabled = user.get('is_2fa_enabled', False)

                if is_2fa_enabled:
                    # 2FA включена → отправляем код
                    code = generate_2fa_code()
                    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
                    send_2fa_email(email, code)

                    cur.execute("""
                        INSERT INTO email_2fa_codes (email, code, expires_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (email)
                        DO UPDATE SET code = EXCLUDED.code, expires_at = EXCLUDED.expires_at
                    """, (email, code, expires_at))
                    conn.commit()

                    return jsonify(success=True, message="Verification code sent to your email."), 200

                else:
                    # 2FA выключена → сразу JWT
                    access_token = create_access_token(identity=username)
                    return jsonify(success=True, token=access_token, username=username), 200

            else:
                return jsonify(success=False, message="Invalid email or password"), 401

    except Exception as e:
        print("Login error:", str(e))
        return jsonify(success=False, message="Server error"), 500


    return jsonify(success=False, message="Invalid email or password"), 401

    
        
@auth_bp.route("/verify-2fa", methods=["POST"])
def verify_2fa():
    data = request.get_json()
    email = data.get("email", "").strip()
    code_input = str(data.get("code", "")).strip()

    if not email or not code_input:
        return jsonify(success=False, message="Email and code are required."), 400

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT code, expires_at FROM email_2fa_codes WHERE email = %s", (email,))
            record = cur.fetchone()

            if not record:
                return jsonify(success=False, message="No verification code found."), 404

            if datetime.utcnow() > record["expires_at"]:
                return jsonify(success=False, message="Verification code expired."), 400

            if code_input != record["code"]:
                return jsonify(success=False, message="Invalid verification code."), 401

            # Удалить использованный код
            cur.execute("DELETE FROM email_2fa_codes WHERE email = %s", (email,))
            conn.commit()

            # Получить username для JWT
            cur.execute("SELECT username FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                return jsonify(success=False, message="User not found."), 404

            # Выдать токен
            access_token = create_access_token(identity=user["username"])
            return jsonify(success=True, token=access_token, username=user["username"]), 200

    except Exception as e:
        print("2FA verification error:", str(e))
        return jsonify(success=False, message="Server error"), 500




@auth_bp.route("/github")
def github_login():
    if not github.authorized:
        return redirect(url_for("github.login"))  # ← запускает GitHub OAuth
    return redirect("/api/github/callback")  # ← сюда, где ты выдаёшь JWT и редирект на фронт


@auth_bp.route("/github/callback")
def github_callback():
    if not github.authorized:
        return redirect(url_for("github.login"))

    resp = github.get("/user")
    profile = resp.json()
    username = profile.get("login")
    email_resp = github.get("/user/emails")
    email_list = email_resp.json()
    email = next((e["email"] for e in email_list if e["primary"]), None)

    if not username:
        return jsonify(success=False, message="GitHub login failed"), 400

    # Сохраняем в users, если нужно
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, generate_password_hash("github_dummy"))
            )
            conn.commit()

    access_token = create_access_token(identity=username)
    from urllib.parse import quote  # добавь в начало файла
    
    encoded_token = quote(access_token)
    return redirect(f"http://localhost:3000/login-success?token={encoded_token}&username={username}")




