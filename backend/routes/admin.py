from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# Декоратор: проверка, что юзер — админ
def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        username = get_jwt_identity()
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT role FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            if not row or row["role"] != 'admin':
                return jsonify(success=False, message="Admin access required"), 403
        return fn(*args, **kwargs)
    return wrapper

# 📥 Получить всех пользователей
@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def get_all_users():
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, username, email, role, is_subscribed, is_2fa_enabled FROM users")
        users = cur.fetchall()
    return jsonify(users)

# ✈️ Получить все поездки
@admin_bp.route("/trips", methods=["GET"])
@jwt_required()
@admin_required
def get_all_trips():
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT trips.id, trips.name, trips.date_start, trips.date_end, users.username AS creator_username
            FROM trips
            JOIN users ON trips.creator_id = users.id
        """)
        trips = cur.fetchall()
    return jsonify(trips)

# 🗳️ Получить все голосования
@admin_bp.route("/votes", methods=["GET"])
@jwt_required()
@admin_required
def get_all_votes():
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT voting_sessions.id, title, status, expires_at, users.username AS creator_username
            FROM voting_sessions
            JOIN users ON voting_sessions.creator_id = users.id
        """)
        votes = cur.fetchall()
    return jsonify(votes)

from flask import jsonify
from psycopg2 import errors  # ForeignKeyViolation и др.

# Удаление пользователя (кроме админа)
@admin_bp.route("/users/<string:user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id):
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            # Защитимся от удаления админа прямо в DELETE
            cur.execute("""
                DELETE FROM users
                WHERE id = %s::uuid AND role <> 'admin'
                RETURNING id, role
            """, (user_id,))
            row = cur.fetchone()

        if row is None:
            # либо юзер не существует, либо он админ
            # проверим отдельно, чтобы отдать корректное сообщение
            with get_db_connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT role FROM users WHERE id = %s::uuid", (user_id,))
                r = cur.fetchone()
            if r and r[0] == 'admin':
                return jsonify(success=False, message="Cannot delete admin user!"), 400
            return jsonify(success=False, message="User not found"), 404

        return jsonify(success=True), 200

    except errors.ForeignKeyViolation as e:
        # Если вдруг осталась жесткая ссылка на users (например, notifications)
        return jsonify(success=False, error="FK violation", detail=str(e)), 409
    except Exception as e:
        print("[DELETE USER ERROR]", e)
        return jsonify(success=False, message="Internal server error"), 500


# Удаление поездки
@admin_bp.route("/trips/<string:trip_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_trip(trip_id):
    conn = get_db_connection()
    try:
        with conn, conn.cursor() as cur:
            # 1) Явно проверим, есть ли строка
            cur.execute("SELECT 1 FROM trips WHERE id = %s::uuid", (trip_id,))
            exists = cur.fetchone() is not None
            print("[DELETE TRIP] hit", trip_id, "exists:", exists)

            if not exists:
                return jsonify(success=False, message="Trip not found (precheck)"), 404

            # 2) Удаляем
            cur.execute("DELETE FROM trips WHERE id = %s::uuid RETURNING id", (trip_id,))
            row = cur.fetchone()

        if not row:
            # сюда попадёшь только при гонке между SELECT и DELETE
            print("[DELETE TRIP] race: deleted by someone else")
            return jsonify(success=False, message="Trip not found (race)"), 404

        return jsonify(success=True), 200

    except errors.ForeignKeyViolation as e:
        return jsonify(success=False, message="Trip has dependent records", detail=str(e)), 409
    except Exception as e:
        print("[DELETE TRIP ERROR]", e)
        return jsonify(success=False, message="Internal server error"), 500


# Удаление голосования (UUID)
@admin_bp.route("/votes/<string:vote_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_vote(vote_id):
    print("[DELETE VOTE] hit", vote_id)
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            # precheck: есть ли такая сессия?
            cur.execute("SELECT 1 FROM voting_sessions WHERE id = %s::uuid", (vote_id,))
            exists = cur.fetchone() is not None
            print("[DELETE VOTE] exists:", exists)
            if not exists:
                return jsonify(success=False, message="Voting session not found"), 404

            cur.execute(
                "DELETE FROM voting_sessions WHERE id = %s::uuid RETURNING id;",
                (vote_id,)
            )
            row = cur.fetchone()

        if not row:
            # гонка: кто-то удалил между SELECT и DELETE
            return jsonify(success=False, message="Voting session not found (race)"), 404

        return jsonify(success=True), 200

    except errors.ForeignKeyViolation as e:
        return jsonify(
            success=False,
            message="Voting session cannot be deleted due to existing references",
            detail=str(e),
            hint="Delete related votes first or add ON DELETE CASCADE"
        ), 409
    except Exception as e:
        print("[DELETE VOTE ERROR]", e)
        return jsonify(success=False, message="Internal server error"), 500
