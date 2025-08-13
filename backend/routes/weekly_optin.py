# routes/weekly_optin.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection

weekly_optin_bp = Blueprint("weekly_optin", __name__, url_prefix="/api/user")

@weekly_optin_bp.route("/weekly-optin", methods=["GET"])
@jwt_required()
def get_weekly_optin():
    username = get_jwt_identity()
    conn = get_db_connection()
    with conn, conn.cursor() as cur:
        cur.execute("SELECT weekly_trip_opt_in FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
    return jsonify(success=True, weekly_trip_opt_in=bool(row and row.get("weekly_trip_opt_in")))

@weekly_optin_bp.route("/weekly-optin", methods=["PATCH"])
@jwt_required()
def set_weekly_optin():
    username = get_jwt_identity()
    enabled = bool((request.get_json() or {}).get("enabled"))
    conn = get_db_connection()
    with conn, conn.cursor() as cur:
        cur.execute("UPDATE users SET weekly_trip_opt_in=%s WHERE username=%s", (enabled, username))
    return jsonify(success=True, weekly_trip_opt_in=enabled)
