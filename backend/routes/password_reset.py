from flask import Blueprint, request, jsonify
from db import get_db_connection
from datetime import datetime, timedelta, timezone
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from utils.email_notify import send_email_notification, generate_2fa_code

reset_bp = Blueprint("password_reset", __name__, url_prefix="/api")

@reset_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email", "").strip()

    if not email:
        return jsonify(success=False, message="Email is required"), 400

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT username FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                return jsonify(success=False, message="Email not found"), 404

            code = generate_2fa_code()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

            cur.execute("""
                INSERT INTO email_2fa_codes (email, code, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (email)
                DO UPDATE SET code = EXCLUDED.code, expires_at = EXCLUDED.expires_at
            """, (email, code, expires_at))

            send_email_notification(
                username=user["username"],
                subject="Password Reset Code",
                message=f"Your TripDVisor password reset code is: {code} (valid for 10 minutes)"
            )

            conn.commit()
        return jsonify(success=True, message="Reset code sent to email"), 200

    except Exception as e:
        print("❌ Forgot password error:", str(e))
        return jsonify(success=False, message="Server error"), 500


@reset_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email", "").strip()
    code = str(data.get("code", "")).strip()
    new_password = data.get("password", "")

    if not all([email, code, new_password]):
        return jsonify(success=False, message="All fields are required"), 400

    if len(new_password) < 8 or not any(c.isdigit() for c in new_password):
        return jsonify(success=False, message="Password must be at least 8 characters and contain digits"), 400

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Проверка кода
            cur.execute("SELECT code, expires_at FROM email_2fa_codes WHERE email = %s", (email,))
            record = cur.fetchone()

            if not record:
                return jsonify(success=False, message="Reset code not found"), 404
            if datetime.utcnow() > record["expires_at"]:
                return jsonify(success=False, message="Reset code expired"), 400
            if code != record["code"]:
                return jsonify(success=False, message="Invalid reset code"), 401

            # 2. Обновляем пароль
            hashed = generate_password_hash(new_password)
            cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed, email))

            # 3. Удаляем использованный код
            cur.execute("DELETE FROM email_2fa_codes WHERE email = %s", (email,))

            # 4. Получаем username и отправляем уведомление
            cur.execute("SELECT username FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user:
                send_email_notification(
                    username=user["username"],
                    subject="Password Successfully Changed",
                    message="Your TripDVisor password has been updated successfully. If this wasn't you, please contact support."
                )

            conn.commit()
            return jsonify(success=True, message="Password successfully updated"), 200

    except Exception as e:
        print("❌ Reset password error:", str(e))
        return jsonify(success=False, message="Server error"), 500
