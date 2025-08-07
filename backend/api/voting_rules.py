from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from datetime import datetime

voting_bp = Blueprint("voting", __name__, url_prefix="/api/voting-rules")

@voting_bp.route("", methods=["POST"])
@jwt_required()
def create_voting_rule():
    username = get_jwt_identity()
    data = request.get_json()

    trip_id = data.get("trip_id")
    approval_threshold = data.get("approval_threshold", 0.7)
    min_votes_required = data.get("min_votes_required", 3)
    duration_hours = data.get("duration_hours", 24)
    rule_type = data.get("rule_type", "majority")

    if not trip_id:
        return jsonify(success=False, message="Trip ID is required."), 400

    try:
        approval_threshold = float(approval_threshold)
        if not (0 < approval_threshold <= 1):
            raise ValueError
    except ValueError:
        return jsonify(success=False, message="Threshold must be a float between 0 and 1"), 400

    try:
        min_votes_required = int(min_votes_required)
        duration_hours = int(duration_hours)
    except ValueError:
        return jsonify(success=False, message="min_votes and duration must be integers"), 400

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                # Получаем user_id по username
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found"), 404
                user_id = user_row["id"]

                # Проверяем, что этот пользователь — creator поездки
                cur.execute("SELECT creator_id FROM trips WHERE id = %s", (trip_id,))
                trip_row = cur.fetchone()
                if not trip_row or trip_row["creator_id"] != user_id:
                    return jsonify(success=False, message="Unauthorized or trip not found"), 403

                # Вставляем правило голосования
                cur.execute("""
                    INSERT INTO voting_rules (trip_id, approval_threshold, min_votes_required, duration_hours, rule_type)
                    VALUES (%s, %s, %s, %s, %s)
                """, (trip_id, approval_threshold, min_votes_required, duration_hours, rule_type))

        return jsonify(success=True, message="Voting rule created"), 201

    except Exception as e:
        print("Voting rule creation error:", str(e))
        return jsonify(success=False, message="Server error"), 500
