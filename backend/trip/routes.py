# trip/routes.py

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import trip_bp
from .models import create_trip, get_trip_by_id, update_trip, delete_trip, list_user_trips

@trip_bp.route('/api/trip', methods=['POST'])
@jwt_required()
def create_trip_route():
    data = request.get_json()
    name = data.get("name")
    date_start = data.get("date_start")
    date_end = data.get("date_end")

    if not name or not date_start or not date_end:
        return jsonify(success=False, message="Missing fields"), 400

    email = get_jwt_identity()  # now string: email
    try:
        trip_id = create_trip(name, email, date_start, date_end)
        return jsonify(success=True, trip_id=trip_id), 201
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@trip_bp.route('/api/trip/<int:trip_id>', methods=['GET'])
@jwt_required()
def get_trip_route(trip_id):
    try:
        trip = get_trip_by_id(trip_id)
        if not trip:
            return jsonify(success=False, message="Trip not found"), 404
        return jsonify(success=True, trip=trip), 200
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@trip_bp.route('/api/trip/<int:trip_id>', methods=['PUT'])
@jwt_required()
def update_trip_route(trip_id):
    data = request.get_json()
    name = data.get("name")
    date_start = data.get("date_start")
    date_end = data.get("date_end")

    if not name or not date_start or not date_end:
        return jsonify(success=False, message="Missing fields"), 400

    email = get_jwt_identity()

    try:
        updated = update_trip(trip_id, email, name, date_start, date_end)
        if updated:
            return jsonify(success=True, message="Trip updated")
        return jsonify(success=False, message="Unauthorized or not found"), 404
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@trip_bp.route('/api/trip/<int:trip_id>', methods=['DELETE'])
@jwt_required()
def delete_trip_route(trip_id):
    email = get_jwt_identity()
    try:
        deleted = delete_trip(trip_id, email)
        if deleted:
            return jsonify(success=True, message="Trip deleted")
        return jsonify(success=False, message="Unauthorized or not found"), 404
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@trip_bp.route('/api/trips', methods=['GET'])
@jwt_required()
def list_trips_route():
    email = get_jwt_identity()
    try:
        trips = list_user_trips(email)
        return jsonify(success=True, trips=trips)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
