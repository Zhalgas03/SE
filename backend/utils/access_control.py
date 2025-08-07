# utils/access_control.py
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from db import get_db_connection
from psycopg2.extras import RealDictCursor

def access_control(require_login=True, require_subscription=False, roles_allowed=None):
    """
    Middleware decorator for controlling access to routes based on:
    - login requirement (JWT)
    - active subscription status
    - user role (e.g., 'admin', 'premium', etc.)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            username = None

            if require_login:
                try:
                    verify_jwt_in_request()
                    username = get_jwt_identity()
                except Exception:
                    return jsonify(success=False, error="Authentication required"), 401

            if require_subscription or roles_allowed:
                try:
                    conn = get_db_connection()
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        cur.execute(
                            "SELECT role, is_subscribed FROM users WHERE username = %s",
                            (username,)
                        )
                        result = cur.fetchone()

                    conn.close()

                    if not result:
                        return jsonify(success=False, error="User not found"), 404

                    role = result["role"]
                    is_subscribed = result["is_subscribed"]

                    if roles_allowed and role not in roles_allowed:
                        return jsonify(success=False, error="Access forbidden (role restriction)"), 403

                    if require_subscription and not is_subscribed:
                        return jsonify(success=False, error="Subscription required"), 403

                except Exception as e:
                    print("[ACCESS CONTROL ERROR]", str(e))
                    return jsonify(success=False, error="Access check failed"), 500

            return fn(*args, **kwargs)
        return wrapper
    return decorator
