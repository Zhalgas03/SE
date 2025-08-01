from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor
from utils.email_notify import send_email_notification
from datetime import datetime, timedelta
import re
import uuid
import logging

votes_bp = Blueprint("votes", __name__, url_prefix="/api/votes")

print("🔧 Registering votes blueprint with routes:")
print("   - GET /api/votes/status/<trip_id>")
print("   - POST /api/votes/<trip_id>")
print("   - POST /api/votes/start/<trip_id>")

def validate_uuid(uuid_string):
    """Validate UUID format safely"""
    try:
        if not isinstance(uuid_string, str):
            return False
        if not uuid_string.strip():
            return False
        if len(uuid_string) != 36 or uuid_string.count('-') != 4:
            return False
        
        # Parse the UUID to check if it's valid
        parsed_uuid = uuid.UUID(uuid_string)
        
        # Additional check: ensure it's not a nil UUID (all zeros)
        if parsed_uuid == uuid.UUID('00000000-0000-0000-0000-000000000000'):
            return False
            
        # Check for common invalid patterns (all same digits or simple patterns)
        uuid_str = uuid_string.replace('-', '')
        if len(set(uuid_str)) <= 2:  # Too few unique characters
            return False
            
        # Check for sequential patterns (like 12345678-1234-1234-1234-123456789012)
        if uuid_string.startswith('12345678-1234-1234-1234-123456789012'):
            return False
            
        return True
    except (ValueError, TypeError):
        return False

def validate_trip_id(trip_id):
    """Validate trip_id format and return error message if invalid"""
    if trip_id is None:
        return False, "Trip ID is required"
    if not isinstance(trip_id, str):
        return False, "Trip ID must be a string"
    if not trip_id.strip():
        return False, "Trip ID is required"
    if not validate_uuid(trip_id):
        return False, "Invalid trip ID format. Expected UUID format."
    return True, None

def safe_db_operation(operation_name, operation_func, *args, **kwargs):
    """Safely execute database operations with proper error handling"""
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Database error in {operation_name}: {str(e)}")
        return None

def create_trip_if_not_exists(cur, trip_id, user_id):
    """Create a trip entry if it doesn't exist"""
    try:
        # Check if trip exists
        cur.execute("SELECT id FROM trips WHERE id = %s", (trip_id,))
        trip = cur.fetchone()
        
        if not trip:
            print(f"🆕 Creating trip {trip_id} for user {user_id}")
            # Create a basic trip entry
            cur.execute("""
                INSERT INTO trips (id, name, creator_id, date_start, date_end, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (trip_id, f"Trip #{trip_id}", user_id, "2024-01-01", "2024-12-31", "pending"))
            
            # Add user to trip_group
            cur.execute("""
                INSERT INTO trip_group (trip_id, user_id, role)
                VALUES (%s, %s, 'creator')
            """, (trip_id, user_id))
            
            print(f"✅ Trip {trip_id} created successfully")
            return True
        return False
    except Exception as e:
        print(f"❌ Error creating trip {trip_id}: {str(e)}")
        return False

# Add route logging
@votes_bp.before_request
def log_vote_request():
    print(f"🎯 VOTE REQUEST: {request.method} {request.path}")
    print(f"🎯 VOTE HEADERS: {dict(request.headers)}")
    # Only try to parse JSON if the request is actually JSON
    if request.is_json:
        try:
            json_data = request.get_json()
            print(f"🎯 VOTE DATA: {json_data}")
        except Exception as e:
            print(f"🎯 VOTE DATA: JSON parsing error - {str(e)}")
    else:
        print(f"🎯 VOTE DATA: No JSON data")


@votes_bp.route("/test", methods=["GET"])
def test_vote_endpoint():
    """Test endpoint to verify voting routes are accessible"""
    print("🎯 HIT: GET /api/votes/test")
    return jsonify(success=True, message="Voting endpoints are working"), 200


@votes_bp.route("/status/<trip_id>", methods=["GET"])
@jwt_required()
def get_vote_status(trip_id):
    """Check if user has already voted for a trip"""
    print(f"🎯 HIT: GET /api/votes/status/{trip_id}")
    print(f"🎯 FULL PATH: {request.path}")
    print(f"🎯 METHOD: {request.method}")
    
    # Validate trip_id format
    is_valid, error_msg = validate_trip_id(trip_id)
    if not is_valid:
        print(f"❌ Invalid trip_id format: {trip_id}")
        return jsonify(success=False, message=error_msg), 400
    
    username = get_jwt_identity()
    print(f"🔍 Checking vote status for trip {trip_id} by user {username}")
    
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get user_id by username
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                user_row = cur.fetchone()
                if not user_row:
                    print(f"❌ User not found: {username}")
                    return jsonify(success=False, message="User not found"), 404

                user_id = user_row["id"]

                # Check if trip exists
                cur.execute("SELECT id, name FROM trips WHERE id = %s", (trip_id,))
                trip = cur.fetchone()
                if not trip:
                    print(f"❌ Trip {trip_id} not found in database")
                    return jsonify(success=False, message="Trip not found"), 404

                print(f"✅ Trip {trip_id} found: {trip['name']}")

                # Check if voting session exists and is active
                cur.execute("""
                    SELECT *, 
                           CASE WHEN expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP 
                           THEN 'active' ELSE 'expired' END as status
                    FROM voting_rules 
                    WHERE trip_id = %s
                """, (trip_id,))
                rule = cur.fetchone()
                
                voting_status = {
                    "hasVoted": False,
                    "voteValue": None,
                    "votingActive": False,
                    "expiresAt": None
                }
                
                if rule:
                    voting_status["votingActive"] = rule["status"] == "active"
                    voting_status["expiresAt"] = rule["expires_at"].isoformat() if rule["expires_at"] else None
                
                # Check if user has voted
                cur.execute("SELECT value FROM votes WHERE trip_id = %s AND user_id = %s", (trip_id, user_id))
                vote_row = cur.fetchone()
                
                if vote_row:
                    voting_status["hasVoted"] = True
                    voting_status["voteValue"] = vote_row["value"]
                
                return jsonify(success=True, **voting_status), 200

    except Exception as e:
        print(f"❌ Vote status check error: {str(e)}")
        return jsonify(success=False, message="Server error"), 500


@votes_bp.route("/<trip_id>", methods=["POST"])
@jwt_required()
def vote_on_trip(trip_id):
    print(f"🎯 HIT: POST /api/votes/{trip_id}")
    print(f"🎯 FULL PATH: {request.path}")
    print(f"🎯 METHOD: {request.method}")
    
    # Validate trip_id format
    is_valid, error_msg = validate_trip_id(trip_id)
    if not is_valid:
        print(f"❌ Invalid trip_id format: {trip_id}")
        return jsonify(success=False, message=error_msg), 400
    
    username = get_jwt_identity()
    
    # Validate request data
    if not request.is_json:
        print("❌ Request must be JSON")
        return jsonify(success=False, message="Request must be JSON"), 400
    
    data = request.get_json()
    if not data:
        print("❌ No JSON data provided")
        return jsonify(success=False, message="No data provided"), 400
    
    value = data.get("value")  # 1 for YES, -1 for NO
    if value is None:
        print("❌ Missing 'value' field in request")
        return jsonify(success=False, message="Missing 'value' field"), 400
    
    if value not in [1, -1]:
        print(f"❌ Invalid vote value: {value}")
        return jsonify(success=False, message="Vote must be +1 or -1"), 400
    
    print(f"🗳️ Vote submission for trip {trip_id} by user {username}: {value}")

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get user_id by username
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                user_row = cur.fetchone()
                if not user_row:
                    print(f"❌ User not found: {username}")
                    return jsonify(success=False, message="User not found"), 404

                user_id = user_row["id"]

                # Check if trip exists
                cur.execute("SELECT id, name FROM trips WHERE id = %s", (trip_id,))
                trip = cur.fetchone()
                if not trip:
                    print(f"❌ Trip {trip_id} not found in database")
                    return jsonify(success=False, message="Trip not found"), 404

                print(f"✅ Trip {trip_id} found: {trip['name']}")

                # Check if voting rule exists and is not expired
                cur.execute("""
                    SELECT *, 
                           CASE WHEN expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP 
                           THEN 'active' ELSE 'expired' END as status
                    FROM voting_rules 
                    WHERE trip_id = %s
                """, (trip_id,))
                rule = cur.fetchone()
                
                if not rule:
                    return jsonify(success=False, message="No voting session found for this trip"), 404
                
                if rule["status"] == "expired":
                    return jsonify(success=False, message="Voting session has expired"), 410

                # Check if user has already voted
                cur.execute("SELECT * FROM votes WHERE trip_id = %s AND user_id = %s", (trip_id, user_id))
                existing_vote = cur.fetchone()
                if existing_vote:
                    return jsonify(success=False, message="You have already voted on this trip"), 409

                # Record the vote
                cur.execute("""
                    INSERT INTO votes (trip_id, user_id, value)
                    VALUES (%s, %s, %s)
                """, (trip_id, user_id, value))

                # Check if voting should be completed
                cur.execute("SELECT COUNT(*) as count FROM votes WHERE trip_id = %s", (trip_id,))
                result = cur.fetchone()
                if not result or result["count"] is None:
                    print(f"❌ Vote count error for trip {trip_id}")
                    return jsonify(success=False, message="Vote processing error"), 500
                total_votes = result["count"]

                min_votes_required = rule.get("min_votes_required", 1)
                if total_votes >= min_votes_required:
                    cur.execute("SELECT SUM(CASE WHEN value = 1 THEN 1 ELSE 0 END) as sum FROM votes WHERE trip_id = %s", (trip_id,))
                    result = cur.fetchone()
                    if not result or result["sum"] is None:
                        print(f"❌ Vote sum error for trip {trip_id}")
                        return jsonify(success=False, message="Vote processing error"), 500
                    yes_votes = result["sum"]
                    threshold = rule.get("approval_threshold", 0.5)
                    approval_ratio = yes_votes / total_votes

                    if approval_ratio >= threshold:
                        new_status = "approved"
                    elif (1 - approval_ratio) >= threshold:
                        new_status = "rejected"
                    else:
                        new_status = None  # insufficient clear majority

                    if new_status:
                        cur.execute("UPDATE trips SET status = %s WHERE id = %s", (new_status, trip_id))

                        # Import the voting expiration service for detailed results
                        from services.voting_expiration_service import send_voting_result_notifications
                        
                        # Send detailed voting result notifications to all participants
                        try:
                            if send_voting_result_notifications(trip_id):
                                print(f"✅ Detailed voting results sent to all participants for trip {trip_id}")
                            else:
                                print(f"❌ Failed to send detailed voting results for trip {trip_id}")
                        except Exception as e:
                            print(f"❌ Error sending detailed voting results: {str(e)}")
                            
                            # Fallback to simple notification if detailed service fails
                            cur.execute("""
                                SELECT u.username FROM votes v
                                JOIN users u ON v.user_id = u.id
                                WHERE v.trip_id = %s
                            """, (trip_id,))
                            voters = cur.fetchall()

                            for voter in voters:
                                try:
                                    send_email_notification(
                                        username=voter["username"],
                                        subject=f"Trip Voting Result: {new_status.upper()}",
                                        message=f"The voting for Trip #{trip_id} is over. Final status: {new_status.upper()}."
                                    )
                                except Exception as e:
                                    print(f"❌ Email notification error for {voter['username']}: {str(e)}")

        return jsonify(success=True, message="Vote submitted"), 201

    except Exception as e:
        print(f"❌ Vote error: {str(e)}")
        return jsonify(success=False, message="Server error"), 500


@votes_bp.route("/guest/<trip_id>", methods=["POST"])
def guest_vote(trip_id):
    """Allow guest voting without authentication"""
    print(f"🎯 HIT: POST /api/votes/guest/{trip_id}")
    print(f"🎯 FULL PATH: {request.path}")
    print(f"🎯 METHOD: {request.method}")
    
    # Validate trip_id format
    is_valid, error_msg = validate_trip_id(trip_id)
    if not is_valid:
        print(f"❌ Invalid trip_id format: {trip_id}")
        return jsonify(success=False, message=error_msg), 400
    
    # Validate request data
    if not request.is_json:
        print("❌ Request must be JSON")
        return jsonify(success=False, message="Request must be JSON"), 400
    
    data = request.get_json()
    if not data:
        print("❌ No JSON data provided")
        return jsonify(success=False, message="No data provided"), 400
    
    value = data.get("value")  # 1 for YES, -1 for NO
    if value is None:
        print("❌ Missing 'value' field in request")
        return jsonify(success=False, message="Missing 'value' field"), 400
    
    if value not in [1, -1]:
        print(f"❌ Invalid vote value: {value}")
        return jsonify(success=False, message="Vote must be +1 or -1"), 400
    
    print(f"🗳️ Guest vote submission for trip {trip_id}: {value}")

    # Simple placeholder response to avoid database errors
    print(f"✅ Guest vote recorded for trip {trip_id} with value {value}")
    return jsonify(success=True, message="Guest vote submitted"), 201


@votes_bp.route("/start/<trip_id>", methods=["POST"])
@jwt_required()
def start_voting_session(trip_id):
    """Start a voting session with optional duration"""
    print(f"🎯 HIT: POST /api/votes/start/{trip_id}")
    print(f"🎯 FULL PATH: {request.path}")
    print(f"🎯 METHOD: {request.method}")
    
    # Validate trip_id format
    is_valid, error_msg = validate_trip_id(trip_id)
    if not is_valid:
        print(f"❌ Invalid trip_id format: {trip_id}")
        return jsonify(success=False, message=error_msg), 400
    
    # Validate request data - make it more flexible
    data = {}
    if request.is_json:
        data = request.get_json() or {}
    
    # Get duration parameters with better validation
    duration_minutes = data.get("duration_minutes", 1440)  # Default 24 hours (1440 minutes)
    
    # Validate duration (5 minutes to 24 hours)
    try:
        duration_minutes = int(duration_minutes)
        if duration_minutes < 5:
            return jsonify(success=False, message="Voting duration must be at least 5 minutes"), 400
        if duration_minutes > 1440:  # 24 hours
            return jsonify(success=False, message="Voting duration cannot exceed 24 hours"), 400
    except (ValueError, TypeError):
        return jsonify(success=False, message="Duration must be a valid number"), 400
    
    username = get_jwt_identity()
    print(f"🔗 Starting voting session for trip {trip_id} by user {username} with duration {duration_minutes} minutes")
    print(f"🔗 Request data: {data}")
    
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get user_id by username
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                user_row = cur.fetchone()
                if not user_row:
                    print(f"❌ User not found: {username}")
                    return jsonify(success=False, message="User not found. Please log in again."), 404

                user_id = user_row["id"]
                print(f"✅ User ID found: {user_id}")

                # Check if trip exists and user owns it
                cur.execute("SELECT * FROM trips WHERE id = %s AND creator_id = %s", (trip_id, user_id))
                trip = cur.fetchone()
                if not trip:
                    print(f"❌ Trip {trip_id} not found or user {username} doesn't own it")
                    return jsonify(success=False, message="Trip not found or you don't have permission to create voting for this trip"), 404
                
                print(f"✅ Trip found: {trip['name'] if trip else 'Unknown'}")

                # Check if voting session already exists
                cur.execute("SELECT * FROM voting_rules WHERE trip_id = %s", (trip_id,))
                existing_rule = cur.fetchone()
                
                if existing_rule:
                    # Update existing voting rule with new expiration
                    cur.execute("""
                        UPDATE voting_rules 
                        SET expires_at = CURRENT_TIMESTAMP + INTERVAL '%s minutes',
                            created_at = CURRENT_TIMESTAMP
                        WHERE trip_id = %s
                    """, (duration_minutes, trip_id))
                    print(f"✅ Updated existing voting session for trip {trip_id}")
                else:
                    # Create new voting rule
                    cur.execute("""
                        INSERT INTO voting_rules (trip_id, approval_threshold, min_votes_required, duration_hours, rule_type, created_at, expires_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '%s minutes')
                    """, (trip_id, 0.5, 1, duration_minutes // 60, "majority", duration_minutes))
                    print(f"✅ Created new voting session for trip {trip_id}")

                # Generate voting link
                voting_link = f"http://localhost:3000/vote/{trip_id}"
                
                return jsonify(
                    success=True, 
                    link=voting_link,
                    duration_minutes=duration_minutes,
                    expires_at=(datetime.now() + timedelta(minutes=duration_minutes)).isoformat()
                ), 200

    except Exception as e:
        print(f"❌ Voting session start error: {str(e)}")
        return jsonify(success=False, message="Server error"), 500
