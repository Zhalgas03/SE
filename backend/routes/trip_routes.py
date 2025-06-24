from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection  # импорт своей функции

trip_bp = Blueprint('trip_bp', __name__, url_prefix='/api/trips')

@trip_bp.route('', methods=['POST'])
@jwt_required()
def create_trip():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    user = get_jwt_identity()
    
    if not title:
        return jsonify(message="Title is required"), 400

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO trips (title, description, start_date, end_date, owner_id)
                    VALUES (%s, %s, %s, %s, (SELECT id FROM users WHERE email = %s))
                    RETURNING id
                """, (title, description, start_date, end_date, user['email']))
                trip_id = cur.fetchone()['id']

        return jsonify(success=True, trip_id=trip_id), 201

    except Exception as e:
        print("❌ Trip create error:", str(e))
        return jsonify(success=False, message="Trip creation failed"), 500

@trip_bp.route('', methods=['GET'])
@jwt_required()
def get_trips():
    user = get_jwt_identity()

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.* FROM trips t
                JOIN users u ON t.owner_id = u.id
                WHERE u.email = %s
            """, (user['email'],))
            trips = cur.fetchall()
        return jsonify(success=True, trips=trips), 200

    except Exception as e:
        print("❌ Trip fetch error:", str(e))
        return jsonify(success=False, message="Failed to fetch trips"), 500
