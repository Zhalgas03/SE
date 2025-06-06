from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection

poi_bp = Blueprint("poi", __name__, url_prefix="/api/poi")


@poi_bp.route("", methods=["POST"])
@jwt_required()
def propose_poi():
    user = get_jwt_identity()
    data = request.get_json()

    trip_id = data.get("trip_id")
    title = data.get("title")
    description = data.get("description")

    if not all([trip_id, title]):
        return jsonify(success=False, message="Trip ID and title are required."), 400

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                # Найдём пользователя
                cur.execute("SELECT id FROM users WHERE username = %s", (user,))
                user_row = cur.fetchone()
                if not user_row:
                    return jsonify(success=False, message="User not found"), 404
                user_id = user_row['id']

                # Добавим предложение POI
                cur.execute("""
                    INSERT INTO poi_proposals (trip_id, title, description, status, user_id)
                    VALUES (%s, %s, %s, 'pending', %s)
                """, (trip_id, title, description, user_id))

        return jsonify(success=True, message="POI proposal submitted"), 201

    except Exception as e:
        print("POI proposal error:", str(e))
        return jsonify(success=False, message="Server error"), 500


@poi_bp.route("/<int:trip_id>", methods=["GET"])
@jwt_required()
def get_pois_for_trip(trip_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, description, status
                FROM poi_proposals
                WHERE trip_id = %s
            """, (trip_id,))
            pois = cur.fetchall()

        return jsonify(success=True, pois=pois), 200

    except Exception as e:
        print("POI fetch error:", str(e))
        return jsonify(success=False, message="Server error"), 500
