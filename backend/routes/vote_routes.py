from flask import Blueprint, request, jsonify
from models import db, Trip, VotingRule, Vote

vote_routes = Blueprint('vote_routes', __name__, url_prefix='/api')

@vote_routes.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()
    trip_id = data.get('trip_id')
    session_token = data.get('session_token')
    value = data.get('value')
    if not all([trip_id, session_token]) or value not in [1, -1]:
        return jsonify(success=False, message="trip_id, session_token, and value (1 or -1) are required"), 400
    # Ensure only one vote per session_token and trip
    existing = Vote.query.filter_by(trip_id=trip_id, session_token=session_token).first()
    if existing:
        return jsonify(success=False, message="You have already voted for this trip"), 409
    vote = Vote(trip_id=trip_id, session_token=session_token, value=value)
    db.session.add(vote)
    try:
        db.session.commit()
        return jsonify(success=True), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"DB error: {str(e)}"), 500

@vote_routes.route('/vote_status/<int:trip_id>', methods=['GET'])
def vote_status(trip_id):
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
    return jsonify({
        "votes": [{"session_token": v.session_token, "value": v.value} for v in votes],
        "yes_votes": yes_votes,
        "no_votes": no_votes,
        "total_votes": total_votes,
        "status": status
    })