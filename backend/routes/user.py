# routes/user.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor
from models.userclass import UserDict  # можно оставить, даже если не используешь
from utils.notify import create_notification
from utils.email_notify import send_email_notification

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    username = get_jwt_identity()
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                id,
                username,
                email,
                role,
                is_2fa_enabled,
                COALESCE(is_subscribed, false)         AS is_subscribed,
                COALESCE(weekly_trip_opt_in, false)    AS weekly_trip_opt_in
            FROM users
            WHERE username = %s
            """,
            (username,),
        )
        record = cur.fetchone()
        if not record:
            return jsonify(success=False, message="User not found"), 404

        return jsonify(success=True, user=record), 200


@user_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    current_username = get_jwt_identity()
    data = request.get_json() or {}

    new_username = (data.get("username") or "").strip()
    new_email = (data.get("email") or "").strip()

    if not new_username or not new_email:
        return jsonify(success=False, message="Username and email are required"), 400

    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 1
                FROM users
                WHERE (username = %s OR email = %s)
                  AND username <> %s
                """,
                (new_username, new_email, current_username),
            )
            if cur.fetchone():
                return jsonify(success=False, message="Username or email already taken"), 409

            cur.execute(
                """
                UPDATE users
                SET username = %s, email = %s
                WHERE username = %s
                """,
                (new_username, new_email, current_username),
            )

    return jsonify(success=True, message="Profile updated successfully"), 200


@user_bp.route("/2fa/enable-disable", methods=["POST"])
@jwt_required()
def toggle_2fa():
    username = get_jwt_identity()
    data = request.get_json() or {}
    enable_2fa = data.get("enable_2fa")

    if enable_2fa not in [True, False]:
        return jsonify(success=False, message="Missing or invalid 'enable_2fa' (must be true/false)"), 400

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "UPDATE users SET is_2fa_enabled = %s WHERE username = %s",
                    (enable_2fa, username),
                )

                # уведомления пользователю
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                user = cur.fetchone()
                if user:
                    title = "2FA Enabled" if enable_2fa else "2FA Disabled"
                    msg = (
                        "You have enabled two-factor authentication."
                        if enable_2fa
                        else "You have disabled two-factor authentication."
                    )
                    create_notification(user["id"], title, msg)
                    send_email_notification(username=username, subject=title, message=msg)

        return jsonify(success=True, message=f"2FA {'enabled' if enable_2fa else 'disabled'}"), 200

    except Exception as e:
        print("2FA toggle error:", str(e))
        return jsonify(success=False, message="Server error while updating 2FA status"), 500


@user_bp.route("/weekly-trip-opt-in", methods=["POST"])
@jwt_required()
def weekly_trip_opt_in():
    """
    Toggle weekly AI trip emails for the current user.
    Body: { "opt_in": true|false }  (строки 'true'/'false' тоже принимаются)
    """
    username = get_jwt_identity()
    data = request.get_json() or {}
    opt_in = data.get("opt_in", None)

    # допускаем строковые значения
    if isinstance(opt_in, str):
        opt_in = opt_in.strip().lower() in ("true", "1", "yes", "y")

    if not isinstance(opt_in, bool):
        return jsonify(success=False, message="Field 'opt_in' must be boolean"), 400

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET weekly_trip_opt_in = %s
                    WHERE username = %s
                    RETURNING COALESCE(weekly_trip_opt_in, false) AS weekly_trip_opt_in
                    """,
                    (opt_in, username),
                )
                row = cur.fetchone()
                if not row:
                    return jsonify(success=False, message="User not found"), 404

        return jsonify(success=True, weekly_trip_opt_in=row["weekly_trip_opt_in"]), 200

    except Exception as e:
        print("weekly_trip_opt_in error:", str(e))
        return jsonify(success=False, message="DB error while updating weekly trip preference"), 500
