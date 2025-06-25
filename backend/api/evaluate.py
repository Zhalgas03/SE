from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from db import get_db_connection
from datetime import datetime, timedelta

evaluate_bp = Blueprint("evaluate", __name__, url_prefix="/api/votes")

@evaluate_bp.route("/<int:trip_id>/evaluate", methods=["GET"])
@jwt_required()
def evaluate_votes(trip_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Получаем правила голосования для этой поездки
            cur.execute("SELECT approval_threshold, min_votes_required, duration_hours, created_at FROM voting_rules WHERE trip_id = %s", (trip_id,))
            rule = cur.fetchone()
            if not rule:
                return jsonify(success=False, message="No voting rules found for this trip."), 404

            threshold = rule["approval_threshold"]
            min_votes = rule["min_votes_required"]
            duration = rule["duration_hours"]
            created_at = rule["created_at"]
            deadline = created_at + timedelta(hours=duration)

            if datetime.utcnow() < deadline:
                return jsonify(success=False, message="Voting still in progress."), 403

            # Считаем голоса
            cur.execute("SELECT COUNT(*) FROM votes WHERE trip_id = %s", (trip_id,))
            total_votes = cur.fetchone()["count"]

            if total_votes < min_votes:
                return jsonify(success=False, message="Not enough votes."), 400

            cur.execute("SELECT COUNT(*) FROM votes WHERE trip_id = %s AND value = 1", (trip_id,))
            positive_votes = cur.fetchone()["count"]

            ratio = positive_votes / total_votes

            if ratio >= threshold:
                result = "approved"
            else:
                result = "rejected"

            return jsonify(success=True, result=result, ratio=round(ratio, 2), total_votes=total_votes, positive_votes=positive_votes), 200

    except Exception as e:
        print("Evaluation error:", str(e))
        return jsonify(success=False, message="Server error"), 500
