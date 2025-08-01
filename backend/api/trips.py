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
                # Получить ID пользователя по username
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

@trips_bp.route('/save-with-pdf', methods=['POST'])
@jwt_required()
def save_with_pdf():
    user = get_jwt_identity()
    data = request.get_json()
    print(f"Received trip data with PDF from user {user}:", data)
    
    # Validate required fields
    if not data:
        return jsonify(success=False, message="No data provided"), 400
    
    name = data.get("name")
    date_start = data.get("date_start")
    date_end = data.get("date_end")
    pdf_base64 = data.get("pdf_base64")
    
    if not name:
        return jsonify(success=False, message="Trip name is required"), 400
    
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get user ID from username
                cur.execute("SELECT id FROM users WHERE username = %s", (user,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found"), 404
                
                creator_id = user_row['id']
                
                # Save PDF file if provided
                pdf_file_path = None
                if pdf_base64:
                    try:
                        # Create trips directory if it doesn't exist
                        folder = os.path.join(current_app.root_path, "static", "trips")
                        os.makedirs(folder, exist_ok=True)
                        
                        # Generate filename
                        filename = f"{user}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                        abs_path = os.path.join(folder, filename)
                        rel_path = f"static/trips/{filename}"
                        
                        # Handle base64 data with or without data URL prefix
                        if pdf_base64.startswith('data:application/pdf;base64,'):
                            pdf_data = pdf_base64.split(',')[1]
                        else:
                            pdf_data = pdf_base64
                        
                        pdf_bytes = base64.b64decode(pdf_data)
                        
                        # Save PDF file
                        with open(abs_path, "wb") as f:
                            f.write(pdf_bytes)
                        
                        pdf_file_path = rel_path
                        print(f"PDF saved successfully: {abs_path}")
                        
                    except Exception as file_error:
                        print(f"PDF file save error: {str(file_error)}")
                        return jsonify(success=False, message="Failed to save PDF file"), 500
                
                # Insert trip into database
                cur.execute("""
                    INSERT INTO trips (name, creator_id, date_start, date_end, pdf_file_path)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (name, creator_id, date_start, date_end, pdf_file_path))
                
                result = cur.fetchone()
                if not result or "id" not in result:
                    return jsonify(success=False, message="Failed to create trip"), 500
                
                trip_id = result["id"]
                
                # Insert into trip_group
                cur.execute("""
                    INSERT INTO trip_group (trip_id, user_id, role)
                    VALUES (%s, %s, 'creator')
                """, (trip_id, creator_id))
                
                print(f"Trip saved successfully! ID: {trip_id}, PDF: {pdf_file_path}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Trip save with PDF error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message="Server error"), 500


@trips_bp.route("/favorites", methods=["GET"])
@jwt_required()
def get_trips_with_pdf():
    current_user = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM trips WHERE creator_id = (SELECT id FROM users WHERE username = %s) AND pdf_file_path IS NOT NULL ORDER BY created_at DESC",
        (current_user,)
    )
    trips = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"success": True, "trips": trips}), 200


@trips_bp.route("/<trip_id>", methods=["DELETE"])
@jwt_required()
def delete_trip(trip_id):
    current_user = get_jwt_identity()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Получаем путь к PDF только если поездка принадлежит текущему пользователю
    cursor.execute(
        """
        SELECT pdf_file_path FROM trips 
        WHERE id = %s AND creator_id = (
            SELECT id FROM users WHERE username = %s
        )
        """,
        (trip_id, current_user)
    )
    trip = cursor.fetchone()

    if not trip:
        return jsonify({"success": False, "error": "Trip not found or not allowed"}), 404

    # Удаляем PDF-файл (если существует)
    import os
    pdf_path = trip["pdf_file_path"]
    if pdf_path:
        try:
            os.remove(pdf_path)
        except FileNotFoundError:
            pass  # Файл не найден — не критично

    # Удаляем поездку из БД
    cursor.execute("DELETE FROM trips WHERE id = %s", (trip_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"success": True}), 200

