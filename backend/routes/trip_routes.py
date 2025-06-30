<<<<<<< HEAD
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
=======
import os
import json
from flask import Blueprint, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
from models import db, Trip, VotingRule, Vote

trip_routes = Blueprint('trip_routes', __name__, url_prefix='/api')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@trip_routes.route('/save_trip', methods=['POST'])
def save_trip():
    if 'pdf' not in request.files or 'voting_rules' not in request.form or 'title' not in request.form:
        return jsonify(success=False, message="PDF, title, and voting_rules are required"), 400
    pdf_file = request.files['pdf']
    title = request.form['title']
    voting_rules_json = request.form['voting_rules']
    try:
        voting_rules = json.loads(voting_rules_json)
    except Exception:
        return jsonify(success=False, message="Invalid voting_rules JSON"), 400

    filename = secure_filename(pdf_file.filename)
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    pdf_file.save(pdf_path)

    trip = Trip(title=title, pdf_path=pdf_path)
    db.session.add(trip)
    db.session.flush()  # get trip.id
    rule = VotingRule(
        trip_id=trip.id,
        threshold=voting_rules.get('threshold', 1),
        min_votes=voting_rules.get('min_votes', 1),
        max_votes=voting_rules.get('max_votes', 1)
    )
    db.session.add(rule)
    try:
        db.session.commit()
        return jsonify(success=True, trip_id=trip.id), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"DB error: {str(e)}"), 500

@trip_routes.route('/get_trip/<int:trip_id>', methods=['GET'])
def get_trip(trip_id):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        return jsonify(success=False, message="Trip not found"), 404
    rule = trip.voting_rule
    votes = trip.votes
    yes_votes = sum(1 for v in votes if v.value == 1)
    no_votes = sum(1 for v in votes if v.value == -1)
    total_votes = len(votes)
    status = "pending"
    if rule:
        if total_votes >= rule.min_votes:
            ratio = yes_votes / total_votes if total_votes else 0
            if ratio >= rule.threshold:
                status = "approved"
            else:
                status = "rejected"
    download_url = url_for('trip_routes.download_pdf', trip_id=trip.id, _external=True)
    return jsonify({
        "trip_id": trip.id,
        "title": trip.title,
        "created_at": trip.created_at,
        "pdf_path": trip.pdf_path,
        "download_url": download_url,
        "voting_rule": {
            "threshold": rule.threshold if rule else None,
            "min_votes": rule.min_votes if rule else None,
            "max_votes": rule.max_votes if rule else None
        },
        "votes": total_votes,
        "yes_votes": yes_votes,
        "no_votes": no_votes,
        "status": status
    })

@trip_routes.route('/download/<int:trip_id>', methods=['GET'])
def download_pdf(trip_id):
    trip = db.session.get(Trip, trip_id)
    if not trip or not os.path.exists(trip.pdf_path):
        return jsonify(success=False, message="PDF not found"), 404
    return send_file(trip.pdf_path, as_attachment=True, mimetype='application/pdf')
>>>>>>> 276f72e77590322f9f8c422c79f4ba32443e7c4f
