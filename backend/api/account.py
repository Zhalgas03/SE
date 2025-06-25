from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor

account_bp = Blueprint("account", __name__, url_prefix="/api/account")

@account_bp.route("/settings", methods=["GET"])
@jwt_required()
def get_account_settings():
    username = get_jwt_identity()
    if not username:
        return jsonify(success=False, message="Invalid or expired token."), 422

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT username, email FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            if not user:
                return jsonify(success=False, message="User not found"), 404

            return jsonify(success=True, data=user), 200
    except Exception as e:
        print("❌ Error in /settings:", str(e))
        return jsonify(success=False, message="Server error"), 500
