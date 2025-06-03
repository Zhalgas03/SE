from flask import Blueprint, request, jsonify, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from config import Config
from requests_oauthlib import OAuth2Session
from sqlalchemy.exc import SQLAlchemyError
import re
import os

from db import SessionLocal
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


@auth_bp.route("/auth/google")
def google_login():
    google = OAuth2Session(
        Config.GOOGLE_CLIENT_ID,
        redirect_uri=Config.REDIRECT_URI,
        scope=["openid", "email", "profile"]
    )
    auth_url, state = google.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type="offline"
    )
    session["oauth_state"] = state
    return redirect(auth_url)


@auth_bp.route("/auth/google/callback")
def google_callback():
    try:
        google = OAuth2Session(
            Config.GOOGLE_CLIENT_ID,
            state=session.get("oauth_state"),
            redirect_uri=Config.REDIRECT_URI
        )
        token = google.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            authorization_response=request.url
        )
        user_info = google.get("https://www.googleapis.com/oauth2/v1/userinfo").json()

        email = user_info["email"]
        name = user_info.get("name", "GoogleUser")

        db = SessionLocal()
        user = db.query(User).filter_by(email=email).first()

        if not user:
            user = User(username=name, email=email, password=generate_password_hash("google_dummy"))
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(identity=user.email)
        return redirect(f"http://localhost:3000?token={token}&username={user.username}")

    except Exception as e:
        print("Google OAuth error:", str(e))
        return jsonify(success=False, message="OAuth error"), 500


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

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
        db = SessionLocal()
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            return jsonify(success=False, message="Username or email exists."), 409

        new_user = User(username=username, email=email, password=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(identity=email)
        return jsonify(success=True, token=token, username=new_user.username)

    except SQLAlchemyError as e:
        print("❌ Register DB error:", str(e))
        return jsonify(success=False, message="Database error"), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not all([email, password]):
        return jsonify(success=False, message="Email and password required"), 400

    try:
        db = SessionLocal()
        user = db.query(User).filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            token = create_access_token(identity=user.email)
            return jsonify(success=True, token=token, username=user.username)
        else:
            return jsonify(success=False, message="Invalid credentials"), 401

    except SQLAlchemyError as e:
        print("Login DB error:", str(e))
        return jsonify(success=False, message="Server error"), 500
