# routes/user.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor
from models.userclass import UserDict
<<<<<<< HEAD
from utils.notify import create_notification

=======
>>>>>>> 276f72e77590322f9f8c422c79f4ba32443e7c4f

user_bp = Blueprint("user", __name__, url_prefix="/api/user")

@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    username = get_jwt_identity()

    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT username, email, is_2fa_enabled 
            FROM users 
            WHERE username = %s
        """, (username,))
        record = cur.fetchone()
        if not record:
            return jsonify(success=False, message="User not found"), 404

        user = UserDict.from_db_row(record)
        return jsonify(success=True, user=user.__dict__), 200


@user_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    current_username = get_jwt_identity()
    data = request.get_json()

    new_username = data.get("username", "").strip()
    new_email = data.get("email", "").strip()

    if not new_username or not new_email:
        return jsonify(success=False, message="Username and email are required"), 400

    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 1 FROM users 
            WHERE (username = %s OR email = %s) AND username != %s
        """, (new_username, new_email, current_username))
        if cur.fetchone():
            return jsonify(success=False, message="Username or email already taken"), 409

        cur.execute("""
            UPDATE users 
            SET username = %s, email = %s 
            WHERE username = %s
        """, (new_username, new_email, current_username))
        conn.commit()

    return jsonify(success=True, message="Profile updated successfully"), 200


@user_bp.route("/2fa/enable-disable", methods=["POST"])
@jwt_required()
def toggle_2fa():
    username = get_jwt_identity()
    data = request.get_json()
    enable_2fa = data.get("enable_2fa")

    if enable_2fa not in [True, False]:
        return jsonify(success=False, message="Missing or invalid 'enable_2fa' (must be true/false)"), 400

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE users 
                SET is_2fa_enabled = %s 
                WHERE username = %s
            """, (enable_2fa, username))
            conn.commit()
<<<<<<< HEAD
            # получаем user_id по username
            cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if user:
                title = "2FA Enabled" if enable_2fa else "2FA Disabled"
                message = "You have enabled two-factor authentication." if enable_2fa else "You have disabled two-factor authentication."
                create_notification(user["user_id"], title, message)

=======
>>>>>>> 276f72e77590322f9f8c422c79f4ba32443e7c4f

        return jsonify(success=True, message=f"2FA {'enabled' if enable_2fa else 'disabled'}"), 200

    except Exception as e:
        print("2FA toggle error:", str(e))
        return jsonify(success=False, message="Server error while updating 2FA status"), 500
