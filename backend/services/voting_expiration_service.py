#!/usr/bin/env python3
"""
Voting Expiration Service
Handles automatic notification of voting results when sessions expire
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
from psycopg2.extras import RealDictCursor
from utils.email_notify import send_email_notification
from datetime import datetime, timedelta
import logging

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def get_voting_results(trip_id):
    """
    Get detailed voting results for a trip
    Returns: dict with total_votes, yes_votes, no_votes, approval_ratio, outcome
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get voting rule
            cur.execute("""
                SELECT approval_threshold, min_votes_required 
                FROM voting_rules 
                WHERE trip_id = %s
            """, (trip_id,))
            rule = cur.fetchone()
            
            if not rule:
                return None
            
            # Get vote counts
            cur.execute("""
                SELECT 
                    COUNT(*) as total_votes,
                    SUM(CASE WHEN value = 1 THEN 1 ELSE 0 END) as yes_votes,
                    SUM(CASE WHEN value = -1 THEN 1 ELSE 0 END) as no_votes
                FROM votes 
                WHERE trip_id = %s
            """, (trip_id,))
            
            result = cur.fetchone()
            if not result:
                return None
            
            total_votes = result["total_votes"] or 0
            yes_votes = result["yes_votes"] or 0
            no_votes = result["no_votes"] or 0
            
            # Calculate outcome
            if total_votes == 0:
                outcome = "no_votes"
                approval_ratio = 0
            else:
                approval_ratio = yes_votes / total_votes
                threshold = rule.get("approval_threshold", 0.5)
                min_votes_required = rule.get("min_votes_required", 1)
                
                if total_votes < min_votes_required:
                    outcome = "insufficient_votes"
                elif approval_ratio >= threshold:
                    outcome = "approved"
                elif (1 - approval_ratio) >= threshold:
                    outcome = "rejected"
                else:
                    outcome = "no_clear_majority"
            
            return {
                "total_votes": total_votes,
                "yes_votes": yes_votes,
                "no_votes": no_votes,
                "approval_ratio": approval_ratio,
                "outcome": outcome,
                "threshold": rule.get("approval_threshold", 0.5),
                "min_votes_required": rule.get("min_votes_required", 1)
            }
            
    except Exception as e:
        log(f"❌ Error getting voting results for trip {trip_id}: {str(e)}")
        return None

def generate_voting_result_message(trip_id, results, trip_name=None):
    """
    Generate a detailed voting result message
    """
    if not results:
        return "Voting session has ended, but results could not be calculated."
    
    total_votes = results["total_votes"]
    yes_votes = results["yes_votes"]
    no_votes = results["no_votes"]
    outcome = results["outcome"]
    approval_ratio = results["approval_ratio"]
    threshold = results["threshold"]
    min_votes_required = results["min_votes_required"]
    
    # Outcome messages
    outcome_messages = {
        "approved": "APPROVED ✅",
        "rejected": "REJECTED ❌", 
        "insufficient_votes": "INSUFFICIENT VOTES ⚠️",
        "no_clear_majority": "NO CLEAR MAJORITY 🤷",
        "no_votes": "NO VOTES CAST 📭"
    }
    
    outcome_text = outcome_messages.get(outcome, "UNKNOWN")
    
    # Generate message
    message = f"""
🗳️ VOTING RESULTS - {trip_name or f'Trip #{trip_id}'}

The voting session has ended. Here are the final results:

📊 VOTE BREAKDOWN:
• Total votes cast: {total_votes}
• Votes FOR: {yes_votes}
• Votes AGAINST: {no_votes}
• Approval rate: {approval_ratio:.1%}

🎯 OUTCOME: {outcome_text}

📋 DETAILS:
• Required minimum votes: {min_votes_required}
• Approval threshold: {threshold:.1%}
• Actual approval rate: {approval_ratio:.1%}

"""
    
    if outcome == "approved":
        message += "✅ The trip has been APPROVED and will proceed!"
    elif outcome == "rejected":
        message += "❌ The trip has been REJECTED and will not proceed."
    elif outcome == "insufficient_votes":
        message += f"⚠️ Not enough votes were cast (minimum {min_votes_required} required)."
    elif outcome == "no_clear_majority":
        message += "🤷 No clear majority was reached. The trip status remains pending."
    elif outcome == "no_votes":
        message += "📭 No votes were cast during the voting period."
    
    message += f"\n\nVoting session for Trip #{trip_id} has concluded."
    
    return message.strip()

def send_voting_result_notifications(trip_id):
    """
    Send voting result notifications to all participants
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get trip name
            cur.execute("SELECT name FROM trips WHERE id = %s", (trip_id,))
            trip = cur.fetchone()
            trip_name = trip["name"] if trip else None
            
            # Get voting results
            results = get_voting_results(trip_id)
            if not results:
                log(f"❌ Could not get voting results for trip {trip_id}")
                return False
            
            # Get all voters
            cur.execute("""
                SELECT DISTINCT u.username, u.email 
                FROM votes v
                JOIN users u ON v.user_id = u.id
                WHERE v.trip_id = %s
            """, (trip_id,))
            voters = cur.fetchall()
            
            if not voters:
                log(f"⚠️ No voters found for trip {trip_id}")
                return False
            
            # Generate result message
            message = generate_voting_result_message(trip_id, results, trip_name)
            subject = f"Voting Results: {trip_name or f'Trip #{trip_id}'}"
            
            # Send notifications to all voters
            success_count = 0
            for voter in voters:
                try:
                    if send_email_notification(
                        username=voter["username"],
                        subject=subject,
                        message=message
                    ):
                        success_count += 1
                        log(f"✅ Sent voting results to {voter['username']}")
                    else:
                        log(f"❌ Failed to send voting results to {voter['username']}")
                except Exception as e:
                    log(f"❌ Error sending notification to {voter['username']}: {str(e)}")
            
            log(f"📧 Voting results sent to {success_count}/{len(voters)} voters for trip {trip_id}")
            return success_count > 0
            
    except Exception as e:
        log(f"❌ Error in send_voting_result_notifications for trip {trip_id}: {str(e)}")
        return False

def check_and_process_expired_voting_sessions():
    """
    Check for expired voting sessions and send result notifications
    This function should be called periodically (e.g., via cron job)
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Find expired voting sessions that haven't been processed yet
            cur.execute("""
                SELECT vr.trip_id, vr.expires_at, t.name as trip_name
                FROM voting_rules vr
                LEFT JOIN trips t ON vr.trip_id = t.id
                WHERE vr.expires_at <= CURRENT_TIMESTAMP
                AND vr.expires_at IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM voting_notifications vn 
                    WHERE vn.trip_id = vr.trip_id 
                    AND vn.notification_type = 'expiration_results'
                )
                ORDER BY vr.expires_at ASC
            """)
            
            expired_sessions = cur.fetchall()
            
            if not expired_sessions:
                log("✅ No expired voting sessions found")
                return
            
            log(f"📋 Found {len(expired_sessions)} expired voting sessions to process")
            
            processed_count = 0
            for session in expired_sessions:
                trip_id = session["trip_id"]
                expires_at = session["expires_at"]
                trip_name = session["trip_name"]
                
                log(f"📧 Processing expired session for trip {trip_id} (expired at {expires_at})")
                
                # Send notifications
                if send_voting_result_notifications(trip_id):
                    # Mark as processed
                    cur.execute("""
                        INSERT INTO voting_notifications (trip_id, notification_type, sent_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (trip_id, notification_type) DO NOTHING
                    """, (trip_id, "expiration_results"))
                    
                    processed_count += 1
                    log(f"✅ Successfully processed expired session for trip {trip_id}")
                else:
                    log(f"❌ Failed to process expired session for trip {trip_id}")
            
            conn.commit()
            log(f"🎉 Processed {processed_count}/{len(expired_sessions)} expired voting sessions")
            
    except Exception as e:
        log(f"❌ Error in check_and_process_expired_voting_sessions: {str(e)}")
        return False

def create_voting_notifications_table():
    """
    Create the voting_notifications table if it doesn't exist
    This table tracks which notifications have been sent to avoid duplicates
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS voting_notifications (
                    id SERIAL PRIMARY KEY,
                    trip_id UUID NOT NULL,
                    notification_type VARCHAR(50) NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(trip_id, notification_type)
                )
            """)
            conn.commit()
            log("✅ Voting notifications table created/verified")
            return True
    except Exception as e:
        log(f"❌ Error creating voting notifications table: {str(e)}")
        return False

if __name__ == "__main__":
    # Create notifications table
    create_voting_notifications_table()
    
    # Check for expired sessions
    check_and_process_expired_voting_sessions() 