from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from utils import email_notify
from db import get_db_connection
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime
import secrets
import json

def _send_results_email_for_session(session_id: str) -> bool:
    """
    Собирает итоги голосования и отправляет письмо создателю.
    Возвращает True, если отправка выполнена (или уже была), False при ошибке.
    """
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1) Получаем данные по сессии
                cur.execute("""
                    SELECT 
                        vs.id, vs.title, vs.description,
                        vs.results_email_sent,
                        t.name AS trip_name,
                        u.username AS creator_username
                    FROM voting_sessions vs
                    JOIN trips t ON t.id = vs.trip_id
                    JOIN users u ON u.id = vs.creator_id
                    WHERE vs.id = %s
                    LIMIT 1
                """, (session_id,))
                session = cur.fetchone()
                if not session:
                    print(f"[EMAIL] Voting session {session_id} not found")
                    return False

                if session["results_email_sent"]:
                    print(f"[EMAIL] Results email already sent for {session_id}")
                    return True

                # 2) Считаем голоса
                cur.execute("""
                    SELECT 
                        COUNT(*)::int AS total,
                        SUM(CASE WHEN v.value = 1 THEN 1 ELSE 0 END)::int AS votes_for,
                        SUM(CASE WHEN v.value = 0 THEN 1 ELSE 0 END)::int AS votes_against
                    FROM votes v
                    WHERE v.voting_session_id = %s
                """, (session_id,))
                agg = cur.fetchone() or {}
                total = agg.get("total", 0) or 0
                votes_for = agg.get("votes_for", 0) or 0
                votes_against = agg.get("votes_against", 0) or 0

                # 3) Формируем сообщение
                pct_line = ""
                if total > 0:
                    pct_line = f"\nPercentages: For — {votes_for/total*100:.1f}%, Against — {votes_against/total*100:.1f}%"

                subject = f"Voting summary — {session['trip_name']}"
                message = (
                    f"Voting is over: {session['title']}\n\n"
                    f"Trip: {session['trip_name']}\n"
                    f"Description: {session['description'] or '-'}\n\n"
                    f"Summary:\n"
                    f"Total votes : {total}\n"
                    f"For: {votes_for}\n"
                    f"Against: {votes_against}"
                    f"{pct_line}\n\n"
                    f"This is an automatic email."
                )

                # 4) Отправляем
                ok = email_notify.send_email_notification(session["creator_username"], subject, message)

                if ok:
                    cur.execute("""
                        UPDATE voting_sessions
                        SET results_email_sent = TRUE, results_email_sent_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (session_id,))
                return ok
    except Exception as e:
        print(f"[EMAIL ERROR] results email for session {session_id}: {e}")
        return False



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
    user_ip = request.remote_addr  # IP-адрес

    if value not in [0, 1] or not share_link:
        return jsonify(success=False, message="Invalid input"), 400

    conn = get_db_connection()
    session_id_for_email = None
    expired_now = False
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 0) Получаем сессию
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
            # безопасно приводим expected_votes к int (мог прийти строкой)
            expected_votes_raw = rules.get("expected_votes")
            try:
                expected_votes = int(expected_votes_raw) if expected_votes_raw is not None else None
            except (TypeError, ValueError):
                expected_votes = None

            # 1) АВТОЗАКРЫТИЕ ПО ВРЕМЕНИ — на стороне БД (устраняет проблемы TZ)
            cur.execute("""
                UPDATE voting_sessions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND status <> 'completed'
                  AND expires_at IS NOT NULL
                  AND expires_at < CURRENT_TIMESTAMP
                RETURNING id
            """, (session["id"],))
            row = cur.fetchone()
            if row:
                session_id_for_email = row["id"]
                expired_now = True
            else:
                # если уже закрыто — не принимаем голос
                if session["status"] == "completed":
                    return jsonify(success=False, message="Voting session has ended"), 403

                # 2) Проверки анонима/дубликатов
                if not current_user:
                    if not anonymous_allowed:
                        return jsonify(success=False, message="Anonymous voting not allowed"), 403
                    cur.execute("""
                        SELECT 1 FROM votes
                        WHERE voting_session_id = %s AND ip_address = %s
                    """, (session["id"], user_ip))
                    if cur.fetchone():
                        return jsonify(success=False, message="You have already voted from this IP address"), 403

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

                # 3) Сохраняем голос
                cur.execute("""
                    INSERT INTO votes (old_trip_id, value, user_id, comment, voting_session_id, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (session["trip_id"], value, user_id, comment, session["id"], user_ip))

                # 4) Закрытие по количеству (если достигли expected_votes)
                if expected_votes is not None:
                    cur.execute("""
                        SELECT COUNT(*)::int AS cnt
                        FROM votes
                        WHERE voting_session_id = %s
                    """, (session["id"],))
                    count = cur.fetchone()["cnt"]
                    if count >= expected_votes:
                        cur.execute("""
                            UPDATE voting_sessions
                            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                            WHERE id = %s AND status <> 'completed'
                            RETURNING id
                        """, (session["id"],))
                        row2 = cur.fetchone()
                        if row2:
                            session_id_for_email = row2["id"]

    # ВНЕ транзакции — письмо, если закрыли по времени или по количеству
    if session_id_for_email:
        try:
            _send_results_email_for_session(session_id_for_email)
        except Exception as e:
            print(f"[EMAIL ERROR] deferred send for {session_id_for_email}: {e}")

    # Если закрыли прямо сейчас по дедлайну — сообщаем 403
    if expired_now:
        return jsonify(success=False, message="Voting session has ended"), 403

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


@votes_bp.route("/close-expired", methods=["POST"])
@jwt_required()
def close_expired_sessions():
    """
    1) Закрывает все активные сессии с истёкшим дедлайном.
    2) Шлёт письмо по всем завершённым сессиям, у которых ещё не отправляли результаты.
    3) (опционально) Удаляет завершённые сессии после рассылки, если передан ?purge=1
       Удаление каскадное (ON DELETE CASCADE).
    """
    do_purge = request.args.get("purge") in ("1", "true", "yes")

    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # A) Закрываем просроченные активные
            cur.execute("""
                UPDATE voting_sessions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE status <> 'completed'
                  AND expires_at IS NOT NULL
                  AND expires_at < CURRENT_TIMESTAMP
                RETURNING id
            """)
            newly_closed = [r["id"] for r in (cur.fetchall() or [])]

            # B) Собираем все завершённые без отправленного письма
            cur.execute("""
                SELECT id
                FROM voting_sessions
                WHERE status = 'completed'
                  AND COALESCE(results_email_sent, FALSE) = FALSE
            """)
            to_email = [r["id"] for r in (cur.fetchall() or [])]

    # Письма — вне транзакции
    emailed = []
    for sid in to_email:
        try:
            if _send_results_email_for_session(sid):
                emailed.append(sid)
        except Exception as e:
            print(f"[EMAIL ERROR] deferred send for {sid}: {e}")

    deleted_ids = []
    if do_purge:
        # Удаляем только те сессии, по которым письма уже отправлены (чтобы не потерять рассылку)
        # Здесь чистим и те, что уже были completed раньше и имели results_email_sent=true
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    DELETE FROM voting_sessions
                    WHERE status = 'completed'
                      AND COALESCE(results_email_sent, FALSE) = TRUE
                    RETURNING id
                """)
                deleted_ids = [r["id"] for r in (cur.fetchall() or [])]

    return jsonify({
        "success": True,
        "newly_closed_count": len(newly_closed),
        "emailed_count": len(emailed),
        "newly_closed_ids": newly_closed,
        "emailed_ids": emailed,
        "purged": do_purge,
        "deleted_ids": deleted_ids
    }), 200



@votes_bp.route("/send-results/<session_id>", methods=["POST"])
@jwt_required()
def resend_results(session_id):
    """
    Ручная отправка (идемпотентно): если уже отправлено — просто вернёт success.
    Можно повесить проверку на роль админа/создателя.
    """
    ok = _send_results_email_for_session(session_id)
    return jsonify(success=bool(ok)), 200
