from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor
import base64
import os
from datetime import datetime
from flask import current_app

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
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
                result = cur.fetchone()
                if not result or "id" not in result:
                    return jsonify(success=False, message="Failed to create trip."), 500
                trip_id = result["id"]

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
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Получить ID пользователя по email
                cur.execute("SELECT user_id FROM users WHERE username = %s", (user_login,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found"), 404
                user_id = user_row["user_id"]

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

@trips_bp.route("/save-with-pdf", methods=["POST"])
@jwt_required()
def save_trip_with_pdf():
    user = get_jwt_identity()
    data = request.get_json()

    name = data.get("name")
    date_start = data.get("date_start")
    date_end = data.get("date_end")
    pdf_base64 = data.get("pdf_base64")

    if not all([name, pdf_base64]):
        return jsonify(success=False, message="Missing fields"), 400

    try:
        # Получаем ID пользователя
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT user_id FROM users WHERE username = %s", (user,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found"), 404
                user_id = user_row["user_id"]

        # 📁 Генерируем путь и создаём папку (если нужно)
        folder = os.path.join(current_app.root_path, "static", "trips")
        os.makedirs(folder, exist_ok=True)

        filename = f"{user}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        abs_path = os.path.join(folder, filename)
        rel_path = f"static/trips/{filename}"

        # 💾 Сохраняем файл
        with open(abs_path, "wb") as f:
            f.write(base64.b64decode(pdf_base64.split(',')[1]))

        # 📝 Запись в таблицу trips
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO trips (name, creator_id, date_start, date_end, pdf_file_path)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (name, user_id, date_start, date_end, rel_path))
                result = cur.fetchone()
                if not result or "id" not in result:
                    return jsonify(success=False, message="Failed to create trip."), 500
                trip_id = result["id"]

                cur.execute("""
                    INSERT INTO trip_group (trip_id, user_id, role)
                    VALUES (%s, %s, 'creator')
                """, (trip_id, user_id))

        return jsonify(success=True, trip_id=trip_id, pdf_path=rel_path), 201

    except Exception as e:
        print("Trip save with PDF error:", str(e))
        return jsonify(success=False, message="Server error"), 500


@trips_bp.route("/favorites", methods=["GET"])
@jwt_required()
def get_trips_with_pdf():
    current_user = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM trips WHERE creator_id = (SELECT user_id FROM users WHERE username = %s) AND pdf_file_path IS NOT NULL ORDER BY created_at DESC",
        (current_user,)
    )
    trips = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"success": True, "trips": trips}), 200