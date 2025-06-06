from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection

trips_bp = Blueprint("trips", __name__, url_prefix="/api/trips")


@trips_bp.route("", methods=["POST"])
@jwt_required()
def create_trip():
    user = get_jwt_identity()  # ← это username
    print("JWT identity:", user)
    data = request.get_json()

    name = data.get("name")
    date_start = data.get("date_start")
    date_end = data.get("date_end")

    if not name:
        return jsonify(success=False, message="Trip name is required."), 400

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                # Поиск по username
                cur.execute("SELECT id FROM users WHERE username = %s", (user,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found."), 404

                creator_id = user_row['id']

                # Вставка поездки
                cur.execute("""
                    INSERT INTO trips (name, creator_id, date_start, date_end)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, (name, creator_id, date_start, date_end))
                trip_id = cur.fetchone()['id']

                # Вставка в trip_group
                cur.execute("""
                    INSERT INTO trip_group (trip_id, user_id, role)
                    VALUES (%s, %s, 'creator')
                """, (trip_id, creator_id))

        return jsonify(success=True, trip_id=trip_id, message="Trip created"), 201

    except Exception as e:
        print("Trip creation error:", str(e))
        return jsonify(success=False, message="Server error"), 500



@trips_bp.route("", methods=["GET"])
@jwt_required()
def get_trips():
    user_identity = get_jwt_identity()
    user_login = user_identity

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                # Получить ID пользователя по email
                cur.execute("SELECT id FROM users WHERE username = %s", (user_login,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found"), 404
                user_id = user_row["id"]

                # Найти все поездки, в которых участвует пользователь
                cur.execute("""
                    SELECT t.id, t.name, t.date_start, t.date_end, g.role
                    FROM trips t
                    JOIN trip_group g ON t.id = g.trip_id
                    WHERE g.user_id = %s
                    ORDER BY t.date_start
                """, (user_id,))
                trips = cur.fetchall()

        return jsonify(success=True, trips=trips), 200

    except Exception as e:
        print("Trip list error:", str(e))
        return jsonify(success=False, message="Server error"), 500
