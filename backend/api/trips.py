from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor
import base64
import os
from datetime import datetime

trips_bp = Blueprint("trips", __name__, url_prefix="/api/trips")

# --- Создание поездки с PDF ---
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
        conn = get_db_connection()

        # --- Получаем ID пользователя ---
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE username = %s", (user,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found"), 404
                user_id = user_row["id"]

        # --- Сохраняем PDF на диск ---
        folder = os.path.join(current_app.root_path, "static", "trips")
        os.makedirs(folder, exist_ok=True)

        filename = f"{user}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        abs_path = os.path.join(folder, filename)
        rel_path = f"static/trips/{filename}"

        with open(abs_path, "wb") as f:
            f.write(base64.b64decode(pdf_base64.split(',')[1]))

        # --- Записываем поездку в БД ---
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

                # Добавляем пользователя в trip_group
                cur.execute("""
                    INSERT INTO trip_group (trip_id, user_id, role)
                    VALUES (%s, %s, 'creator')
                """, (trip_id, user_id))

        return jsonify(success=True, trip_id=trip_id, pdf_path=rel_path), 201

    except Exception as e:
        print("Trip save with PDF error:", str(e))
        return jsonify(success=False, message="Server error"), 500


# --- Получить все поездки с PDF (favorites) ---
@trips_bp.route("/favorites", methods=["GET"])
@jwt_required()
def get_trips_with_pdf():
    current_user = get_jwt_identity()

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM trips
                    WHERE creator_id = (SELECT id FROM users WHERE username = %s)
                    AND pdf_file_path IS NOT NULL
                    ORDER BY created_at DESC
                """, (current_user,))
                trips = cur.fetchall()

        return jsonify({"success": True, "trips": trips}), 200

    except Exception as e:
        print("Get favorites error:", str(e))
        return jsonify({"success": False, "error": "Server error"}), 500


# --- Удалить поездку и PDF ---
@trips_bp.route("/<trip_id>", methods=["DELETE"])
@jwt_required()
def delete_trip(trip_id):
    current_user = get_jwt_identity()

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Получаем путь к PDF
                cur.execute("""
                    SELECT pdf_file_path FROM trips
                    WHERE id = %s AND creator_id = (
                        SELECT id FROM users WHERE username = %s
                    )
                """, (trip_id, current_user))
                trip = cur.fetchone()

                if not trip:
                    return jsonify({"success": False, "error": "Trip not found or not allowed"}), 404

                pdf_path = trip["pdf_file_path"]

                # Удаляем файл с диска
                if pdf_path:
                    abs_path = os.path.join(current_app.root_path, pdf_path)
                    try:
                        os.remove(abs_path)
                    except FileNotFoundError:
                        pass

                # Удаляем поездку
                cur.execute("DELETE FROM trips WHERE id = %s", (trip_id,))

        return jsonify({"success": True}), 200

    except Exception as e:
        print("Delete trip error:", str(e))
        return jsonify({"success": False, "error": "Server error"}), 500
