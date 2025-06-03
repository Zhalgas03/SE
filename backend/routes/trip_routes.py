from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import Session
from db import SessionLocal
from models.trip import Trip
from datetime import datetime

trip_bp = Blueprint("trip", __name__, url_prefix="/api")

# 🎯 Create a trip
@trip_bp.route("/trip", methods=["POST"])
@jwt_required()
def create_trip():
    data = request.get_json()
    name = data.get("name")
    date_start = data.get("date_start")
    date_end = data.get("date_end")

    if not all([name, date_start, date_end]):
        return jsonify(success=False, message="Missing fields"), 400

    user_email = get_jwt_identity()
    db: Session = SessionLocal()

    try:
        trip = Trip(
            name=name,
            date_start=datetime.strptime(date_start, "%Y-%m-%d"),
            date_end=datetime.strptime(date_end, "%Y-%m-%d"),
            creator_email=user_email
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)

        return jsonify(success=True, trip_id=trip.id), 201

    except Exception as e:
        db.rollback()
        print("❌ Trip create error:", str(e))
        return jsonify(success=False, message="Server error"), 500

    finally:
        db.close()


# 🎯 Get trip by ID
@trip_bp.route("/trip/<int:trip_id>", methods=["GET"])
@jwt_required()
def get_trip(trip_id):
    db: Session = SessionLocal()
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            return jsonify(success=False, message="Trip not found"), 404

        return jsonify(success=True, trip={
            "id": trip.id,
            "name": trip.name,
            "date_start": trip.date_start.isoformat(),
            "date_end": trip.date_end.isoformat(),
            "creator_email": trip.creator_email
        }), 200

    except Exception as e:
        print("❌ Trip fetch error:", str(e))
        return jsonify(success=False, message="Server error"), 500

    finally:
        db.close()


# 🎯 Get all trips for logged-in user
@trip_bp.route("/trips", methods=["GET"])
@jwt_required()
def get_user_trips():
    user_email = get_jwt_identity()
    db: Session = SessionLocal()

    try:
        trips = db.query(Trip).filter(Trip.creator_email == user_email).all()
        return jsonify(success=True, trips=[{
            "id": t.id,
            "name": t.name,
            "date_start": t.date_start.isoformat(),
            "date_end": t.date_end.isoformat()
        } for t in trips]), 200

    except Exception as e:
        print("❌ Get all trips error:", str(e))
        return jsonify(success=False, message="Server error"), 500

    finally:
        db.close()
