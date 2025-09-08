from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, date

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



@admin_bp.route("/analytics", methods=["GET"])
@jwt_required()
@admin_required
def admin_analytics():
    """
    Агрегаты для админ-дашборда.

    Возвращает JSON:
    {
      success: true,
      generated_at: "...",
      totals: {...},
      live: {...},
      ratios: {...},
      series: {
        users_per_month: [{month, cnt}],
        trips_per_month: [{month, cnt}],
        votes_per_month: [{month, cnt}],
        votes_by_status: [{status, cnt}],
        users_by_role: [{role, cnt}]
      },
      trips: {
        avg_duration_days: <float>,
        upcoming_count: <int>,
        top_creators: [{creator_username, cnt}],
        top_names: [{name, cnt}]
      },
      recent: {
        users: [{id, username, created_at, role}],
        trips: [{id, name, date_start, date_end, creator_username}],
        votes: [{id, title, status, expires_at, creator_username}]
      }
    }
    """
    conn = get_db_connection()

    # Границы для помесячных графиков (последние 12 месяцев)
    start_of_this_month = datetime.utcnow().date().replace(day=1)
    since_12m = (start_of_this_month - timedelta(days=365)).replace(day=1)
    since_12m_sql = since_12m.isoformat()

    today_sql = datetime.utcnow().date().isoformat()

    with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        # ---------- Totals ----------
        cur.execute("""
            SELECT
              (SELECT COUNT(*) FROM users)                                         AS users_total,
              (SELECT COUNT(*) FROM users WHERE role = 'admin')                    AS users_admin,
              (SELECT COUNT(*) FROM users WHERE role = 'premium')                  AS users_premium,
              (SELECT COUNT(*) FROM users WHERE COALESCE(is_2fa_enabled,false))    AS users_2fa_enabled,
              (SELECT COUNT(*) FROM trips)                                         AS trips_total,
              (SELECT COUNT(*) FROM trips WHERE date_start::date >= CURRENT_DATE)  AS trips_upcoming,
              (SELECT COUNT(*) FROM voting_sessions)                               AS votes_total,
              (SELECT COUNT(*) FROM voting_sessions WHERE status = 'active')       AS votes_active,
              (SELECT COUNT(*) FROM voting_sessions WHERE status = 'completed')    AS votes_completed
        """)
        totals = cur.fetchone() or {}

        # ---------- Live (за 24 часа и 7 дней) ----------
        cur.execute("""
            SELECT
              (SELECT COUNT(*) FROM users            WHERE created_at >= NOW() - INTERVAL '24 hours') AS users_new_24h,
              (SELECT COUNT(*) FROM trips            WHERE created_at >= NOW() - INTERVAL '24 hours') AS trips_new_24h,
              (SELECT COUNT(*) FROM voting_sessions  WHERE created_at >= NOW() - INTERVAL '24 hours') AS votes_new_24h,
              (SELECT COUNT(*) FROM users            WHERE created_at >= NOW() - INTERVAL '7 days')   AS users_new_7d,
              (SELECT COUNT(*) FROM trips            WHERE created_at >= NOW() - INTERVAL '7 days')   AS trips_new_7d,
              (SELECT COUNT(*) FROM voting_sessions  WHERE created_at >= NOW() - INTERVAL '7 days')   AS votes_new_7d
        """)
        live = cur.fetchone() or {}

        # ---------- Series: помесячные ----------
        cur.execute("""
            SELECT to_char(date_trunc('month', created_at), 'YYYY-MM-01') AS month,
                   COUNT(*)::int AS cnt
            FROM users
            WHERE created_at >= %s
            GROUP BY 1
            ORDER BY 1
        """, (since_12m_sql,))
        users_per_month = cur.fetchall() or []

        cur.execute("""
            SELECT to_char(date_trunc('month', created_at), 'YYYY-MM-01') AS month,
                   COUNT(*)::int AS cnt
            FROM trips
            WHERE created_at >= %s
            GROUP BY 1
            ORDER BY 1
        """, (since_12m_sql,))
        trips_per_month = cur.fetchall() or []

        cur.execute("""
            SELECT to_char(date_trunc('month', created_at), 'YYYY-MM-01') AS month,
                   COUNT(*)::int AS cnt
            FROM voting_sessions
            WHERE created_at >= %s
            GROUP BY 1
            ORDER BY 1
        """, (since_12m_sql,))
        votes_per_month = cur.fetchall() or []

        # ---------- Распределения ----------
        cur.execute("""
            SELECT status, COUNT(*)::int AS cnt
            FROM voting_sessions
            GROUP BY status
            ORDER BY cnt DESC
        """)
        votes_by_status = cur.fetchall() or []

        cur.execute("""
            SELECT role, COUNT(*)::int AS cnt
            FROM users
            GROUP BY role
            ORDER BY cnt DESC
        """)
        users_by_role = cur.fetchall() or []

        # ---------- Trips: средняя длительность, топы ----------
        # Средняя длительность (в днях, включая обе даты)
        cur.execute("""
            SELECT AVG( (date_end::date - date_start::date + 1) )::float AS avg_days
            FROM trips
            WHERE date_end IS NOT NULL AND date_start IS NOT NULL
        """)
        avg_duration_days = (cur.fetchone() or {}).get("avg_days", 0.0) or 0.0

        # Топ-5 создателей по количеству трипов
        cur.execute("""
            SELECT u.username AS creator_username, COUNT(*)::int AS cnt
            FROM trips t
            JOIN users u ON u.id = t.creator_id
            GROUP BY 1
            ORDER BY cnt DESC
            LIMIT 5
        """)
        top_creators = cur.fetchall() or []

        # Топ-8 названий (как у тебя было)
        cur.execute("""
            SELECT LOWER(TRIM(name)) AS name, COUNT(*)::int AS cnt
            FROM trips
            GROUP BY 1
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
            LIMIT 8
        """)
        top_trip_names = cur.fetchall() or []

        # ---------- Recent: последние записи для таблиц ----------
        cur.execute("""
            SELECT id, username, role, created_at
            FROM users
            ORDER BY created_at DESC NULLS LAST
            LIMIT 8
        """)
        recent_users = cur.fetchall() or []

        cur.execute("""
            SELECT t.id, t.name, t.date_start, t.date_end, u.username AS creator_username
            FROM trips t
            JOIN users u ON u.id = t.creator_id
            ORDER BY t.created_at DESC NULLS LAST
            LIMIT 10
        """)
        recent_trips = cur.fetchall() or []

        cur.execute("""
            SELECT v.id, v.title, v.status, v.expires_at, u.username AS creator_username
            FROM voting_sessions v
            JOIN users u ON u.id = v.creator_id
            ORDER BY v.created_at DESC NULLS LAST
            LIMIT 10
        """)
        recent_votes = cur.fetchall() or []

    # ---------- Доп. коэффициенты (на бэке посчитать удобно) ----------
    users_total = int(totals.get("users_total") or 0)
    users_premium = int(totals.get("users_premium") or 0)
    users_2fa_enabled = int(totals.get("users_2fa_enabled") or 0)
    ratios = {
        "premium_share": (users_premium / users_total) if users_total else 0.0,
        "twofa_share": (users_2fa_enabled / users_total) if users_total else 0.0,
    }

    return jsonify({
        "success": True,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "totals": totals,
        "live": live,
        "ratios": ratios,
        "series": {
            "users_per_month": users_per_month,
            "trips_per_month": trips_per_month,
            "votes_per_month": votes_per_month,
            "votes_by_status": votes_by_status,
            "users_by_role": users_by_role,
        },
        "trips": {
            "avg_duration_days": avg_duration_days,
            "upcoming_count": int(totals.get("trips_upcoming") or 0),
            "top_creators": top_creators,
            "top_names": top_trip_names,
        },
        "recent": {
            "users": recent_users,
            "trips": recent_trips,
            "votes": recent_votes,
        }
    })
