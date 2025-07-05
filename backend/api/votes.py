from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor
from utils.email_notify import send_email_notification

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
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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

                # Проверяем, нужно ли завершить голосование
                cur.execute("SELECT COUNT(*) FROM votes WHERE trip_id = %s", (trip_id,))
                result = cur.fetchone()
                if not result or result["count"] is None:
                    return jsonify(success=False, message="Vote count error."), 500
                total_votes = result["count"]

                if total_votes >= rule["min_voters"]:
                    cur.execute("SELECT SUM(CASE WHEN value = 1 THEN 1 ELSE 0 END) FROM votes WHERE trip_id = %s", (trip_id,))
                    result = cur.fetchone()
                    if not result or result["sum"] is None:
                        return jsonify(success=False, message="Vote sum error."), 500
                    yes_votes = result["sum"]
                    threshold = rule["threshold"]
                    approval_ratio = yes_votes / total_votes

                    if approval_ratio >= threshold:
                        new_status = "approved"
                    elif (1 - approval_ratio) >= threshold:
                        new_status = "rejected"
                    else:
                        new_status = None  # недостаточно явного большинства

                    if new_status:
                        cur.execute("UPDATE trips SET status = %s WHERE trip_id = %s", (new_status, trip_id))

                        # Уведомим всех, кто голосовал
                        cur.execute("""
                            SELECT u.username FROM votes v
                            JOIN users u ON v.user_id = u.id
                            WHERE v.trip_id = %s
                        """, (trip_id,))
                        voters = cur.fetchall()

                        for voter in voters:
                            send_email_notification(
                                username=voter["username"],
                                subject=f"Trip Voting Result: {new_status.upper()}",
                                message=f"The voting for Trip #{trip_id} is over. Final status: {new_status.upper()}."
                            )


        return jsonify(success=True, message="Vote submitted"), 201

    except Exception as e:
        print("Vote error:", str(e))
        return jsonify(success=False, message="Server error"), 500