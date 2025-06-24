from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection

votes_bp = Blueprint("votes", __name__, url_prefix="/api/votes")


@votes_bp.route("/<int:trip_id>", methods=["POST"])
@jwt_required()
def vote_on_trip(trip_id):
    username = get_jwt_identity()
    data = request.get_json()
    value = data.get("value")  # 1 for YES, -1 for NO

    if value not in [1, -1]:
        return jsonify(success=False, message="Vote must be +1 or -1"), 400

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

                # Проверяем наличие правила голосования для этой поездки
                cur.execute("SELECT * FROM voting_rules WHERE trip_id = %s", (trip_id,))
                rule = cur.fetchone()
                if not rule:
                    return jsonify(success=False, message="No voting rule defined for this trip"), 404

                # Проверяем, голосовал ли уже пользователь
                cur.execute("SELECT * FROM votes WHERE trip_id = %s AND user_id = %s", (trip_id, user_id))
                existing_vote = cur.fetchone()
                if existing_vote:
                    return jsonify(success=False, message="You have already voted on this trip"), 409

                # Записываем голос
                cur.execute("""
                    INSERT INTO votes (trip_id, user_id, value)
                    VALUES (%s, %s, %s)
                """, (trip_id, user_id, value))

        return jsonify(success=True, message="Vote submitted"), 201

    except Exception as e:
        print("Vote error:", str(e))
        return jsonify(success=False, message="Server error"), 500
