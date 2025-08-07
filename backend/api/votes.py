from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from db import get_db_connection
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime
import secrets
import json


votes_bp = Blueprint("votes", __name__, url_prefix="/api/votes")

@votes_bp.route("/sessions", methods=["POST"])
@jwt_required()
def create_voting_session():
    user = get_jwt_identity()  # username
    data = request.get_json()

    trip_id = data.get("trip_id")
    title = data.get("title")
    description = data.get("description", "")
    expires_at = data.get("expires_at")
    rules = data.get("rules")

    if not all([trip_id, title, expires_at, rules]):
        return jsonify(success=False, message="Missing fields"), 400

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Получаем user_id
                cur.execute("SELECT id FROM users WHERE username = %s", (user,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found"), 404

                user_id = user_row["id"]

                # Проверка: этот пользователь действительно создатель поездки?
                cur.execute("SELECT * FROM trips WHERE id = %s AND creator_id = %s", (trip_id, user_id))
                trip = cur.fetchone()
                if not trip:
                    return jsonify(success=False, message="Trip not found or unauthorized"), 403

                # Генерируем уникальный share_link
                share_link = secrets.token_urlsafe(12)

                # Вставляем voting_session
                cur.execute("""
                    INSERT INTO voting_sessions (
                        id, trip_id, creator_id, title, description, share_link, rules, status, created_at, expires_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, 'active', now(), %s
                    ) RETURNING id
                """, (
                    str(uuid.uuid4()), trip_id, user_id, title, description,
                    share_link, json.dumps(rules), expires_at
                ))

                session_id = cur.fetchone()["id"]

        return jsonify(success=True, voting_session_id=session_id, share_link=share_link), 201

    except Exception as e:
        print("Error creating voting session:", str(e))
        return jsonify(success=False, message="Server error"), 500




@votes_bp.route("/submit", methods=["POST"])
def submit_vote():
    try:
        verify_jwt_in_request()
        current_user = get_jwt_identity()
    except:
        current_user = None

    data = request.get_json()
    share_link = data.get("share_link")
    value = data.get("value")
    comment = data.get("comment")
    user_ip = request.remote_addr  # ← IP-адрес

    if value not in [0, 1] or not share_link:
        return jsonify(success=False, message="Invalid input"), 400

    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT vs.id, vs.trip_id, vs.rules, vs.expires_at, vs.status,
                       u.id AS creator_id
                FROM voting_sessions vs
                JOIN users u ON vs.creator_id = u.id
                WHERE vs.share_link = %s
            """, (share_link,))
            session = cur.fetchone()

            if not session:
                return jsonify(success=False, message="Voting session not found"), 404

            rules = session.get("rules") or {}
            anonymous_allowed = rules.get("anonymous_allowed", False)
            expected_votes = rules.get("expected_votes")

            if session["status"] == "completed" or (session["expires_at"] and session["expires_at"] < datetime.utcnow()):
                return jsonify(success=False, message="Voting session has ended"), 403

            # Если неавторизован — проверка на anonymous_allowed и IP
            if not current_user:
                if not anonymous_allowed:
                    return jsonify(success=False, message="Anonymous voting not allowed"), 403

                cur.execute("""
                    SELECT 1 FROM votes
                    WHERE voting_session_id = %s AND ip_address = %s
                """, (session["id"], user_ip))
                if cur.fetchone():
                    return jsonify(success=False, message="You have already voted from this IP address"), 403

            # Получаем user_id, если есть
            user_id = None
            if current_user:
                cur.execute("SELECT id FROM users WHERE username = %s", (current_user,))
                user_row = cur.fetchone()
                if user_row:
                    user_id = user_row["id"]
                    cur.execute("""
                        SELECT 1 FROM votes
                        WHERE voting_session_id = %s AND user_id = %s
                    """, (session["id"], user_id))
                    if cur.fetchone():
                        return jsonify(success=False, message="You already voted"), 403

            # Сохраняем голос
            cur.execute("""
                INSERT INTO votes (old_trip_id, value, user_id, comment, voting_session_id, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session["trip_id"], value, user_id, comment, session["id"], user_ip))

            # Подсчёт голосов
            cur.execute("""
                SELECT COUNT(*) FROM votes
                WHERE voting_session_id = %s
            """, (session["id"],))
            count = cur.fetchone()["count"]

            if expected_votes and count >= expected_votes:
                cur.execute("""
                    UPDATE voting_sessions
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (session["id"],))

    return jsonify(success=True, message="Vote submitted"), 201


@votes_bp.route("/results/<share_link>", methods=["GET"])
def get_voting_results(share_link):
    print("🔍 Requested share_link:", share_link)

    try:
        verify_jwt_in_request()
        current_user = get_jwt_identity()
    except:
        current_user = None

    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Получаем voting session
            cur.execute("""
                SELECT vs.id, vs.trip_id, vs.rules, vs.status, vs.completed_at,
                       vs.expires_at, vs.title, vs.description
                FROM voting_sessions vs
                WHERE vs.share_link = %s
            """, (share_link,))
            session = cur.fetchone()

            if not session:
                return jsonify(success=False, message="Voting session not found"), 404

            # Считаем голоса
            cur.execute("""
                SELECT
                    v.id, v.value, v.comment, v.created_at,
                    u.username
                FROM votes v
                LEFT JOIN users u ON v.user_id = u.id
                WHERE v.voting_session_id = %s
                ORDER BY v.created_at ASC
            """, (session["id"],))
            votes = cur.fetchall()

            votes_for = sum(1 for v in votes if v["value"] == 1)
            votes_against = sum(1 for v in votes if v["value"] == 0)
            counts = {
                "total": len(votes),
                "for": votes_for,
                "against": votes_against
            }

            # Получаем комментарии
            cur.execute("""
                SELECT 
                    COALESCE(u.username, 'Anonymous') AS username,
                    comment,
                    v.created_at
                FROM votes v
                LEFT JOIN users u ON v.user_id = u.id
                WHERE v.voting_session_id = %s AND comment IS NOT NULL
                ORDER BY v.created_at DESC
            """, (session["id"],))
            comments = cur.fetchall()

            # Проверка: проголосовал ли текущий пользователь
            voted = False
            if current_user:
                cur.execute("SELECT id FROM users WHERE username = %s", (current_user,))
                row = cur.fetchone()
                if row:
                    user_id = row["id"]
                    cur.execute("""
                        SELECT 1 FROM votes 
                        WHERE voting_session_id = %s AND user_id = %s
                    """, (session["id"], user_id))
                    voted = bool(cur.fetchone())

            response = {
                "success": True,
                "status": session["status"],
                "title": session["title"],
                "description": session["description"],
                "rules": session["rules"],
                "expires_at": session["expires_at"],
                "completed_at": session["completed_at"],
                "counts": counts,
                "comments": comments,
                "you_voted": voted
            }
        

    return jsonify(response), 200
