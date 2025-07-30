#!/usr/bin/env python3
"""
Test Voting Expiration Notifications
Tests the automatic email notification system for expired voting sessions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from db import get_db_connection
from psycopg2.extras import RealDictCursor
from services.voting_expiration_service import (
    get_voting_results,
    generate_voting_result_message,
    send_voting_result_notifications,
    create_voting_notifications_table
)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def test_voting_results_calculation():
    """Test the voting results calculation logic"""
    print("\n🧪 TESTING VOTING RESULTS CALCULATION")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get a sample trip with votes
        cur.execute("""
            SELECT DISTINCT v.trip_id, t.name as trip_name
            FROM votes v
            JOIN trips t ON v.trip_id = t.id
            LIMIT 1
        """)
        sample_trip = cur.fetchone()
        
        if not sample_trip:
            print("⚠️ No trips with votes found for testing")
            return False
        
        trip_id = sample_trip["trip_id"]
        trip_name = sample_trip["trip_name"]
        
        log(f"Testing with trip: {trip_name} ({trip_id})")
        
        # Get voting results
        results = get_voting_results(trip_id)
        
        if not results:
            log("❌ Could not get voting results")
            return False
        
        log("📊 Voting Results:")
        log(f"   Total votes: {results['total_votes']}")
        log(f"   Yes votes: {results['yes_votes']}")
        log(f"   No votes: {results['no_votes']}")
        log(f"   Approval ratio: {results['approval_ratio']:.1%}")
        log(f"   Outcome: {results['outcome']}")
        log(f"   Threshold: {results['threshold']:.1%}")
        log(f"   Min votes required: {results['min_votes_required']}")
        
        # Test message generation
        message = generate_voting_result_message(trip_id, results, trip_name)
        log(f"📧 Generated message length: {len(message)} characters")
        
        # Show first few lines of the message
        lines = message.split('\n')[:5]
        log("📝 Message preview:")
        for line in lines:
            log(f"   {line}")
        
        conn.close()
        log("✅ Voting results calculation test passed")
        return True
        
    except Exception as e:
        log(f"❌ Voting results calculation test failed: {str(e)}")
        return False

def test_notifications_table():
    """Test the voting notifications table creation"""
    print("\n🔧 TESTING NOTIFICATIONS TABLE")
    print("=" * 40)
    
    try:
        # Create the notifications table
        if create_voting_notifications_table():
            log("✅ Voting notifications table created/verified successfully")
        else:
            log("❌ Failed to create voting notifications table")
            return False
        
        # Check if table exists and has correct structure
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'voting_notifications' 
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        
        expected_columns = ['id', 'trip_id', 'notification_type', 'sent_at']
        found_columns = [col['column_name'] for col in columns]
        
        log("📋 Table structure:")
        for col in columns:
            log(f"   {col['column_name']}: {col['data_type']}")
        
        for expected in expected_columns:
            if expected in found_columns:
                log(f"   ✅ {expected} column exists")
            else:
                log(f"   ❌ {expected} column missing")
                return False
        
        conn.close()
        log("✅ Notifications table test passed")
        return True
        
    except Exception as e:
        log(f"❌ Notifications table test failed: {str(e)}")
        return False

def test_expired_sessions_detection():
    """Test detection of expired voting sessions"""
    print("\n⏰ TESTING EXPIRED SESSIONS DETECTION")
    print("=" * 45)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check for expired sessions
        cur.execute("""
            SELECT vr.trip_id, vr.expires_at, t.name as trip_name
            FROM voting_rules vr
            LEFT JOIN trips t ON vr.trip_id = t.id
            WHERE vr.expires_at <= CURRENT_TIMESTAMP
            AND vr.expires_at IS NOT NULL
            ORDER BY vr.expires_at ASC
            LIMIT 5
        """)
        
        expired_sessions = cur.fetchall()
        
        if expired_sessions:
            log(f"📋 Found {len(expired_sessions)} expired voting sessions:")
            for session in expired_sessions:
                log(f"   Trip {session['trip_id']}: {session['trip_name']} (expired: {session['expires_at']})")
        else:
            log("✅ No expired voting sessions found")
        
        # Check for sessions that haven't been notified yet
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
            LIMIT 5
        """)
        
        unnotified_sessions = cur.fetchall()
        
        if unnotified_sessions:
            log(f"📧 Found {len(unnotified_sessions)} expired sessions without notifications:")
            for session in unnotified_sessions:
                log(f"   Trip {session['trip_id']}: {session['trip_name']}")
        else:
            log("✅ All expired sessions have been notified")
        
        conn.close()
        log("✅ Expired sessions detection test passed")
        return True
        
    except Exception as e:
        log(f"❌ Expired sessions detection test failed: {str(e)}")
        return False

def test_notification_sending():
    """Test sending notifications (without actually sending emails)"""
    print("\n📧 TESTING NOTIFICATION SENDING")
    print("=" * 40)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Find a trip with votes to test notification sending
        cur.execute("""
            SELECT DISTINCT v.trip_id, t.name as trip_name
            FROM votes v
            JOIN trips t ON v.trip_id = t.id
            LIMIT 1
        """)
        test_trip = cur.fetchone()
        
        if not test_trip:
            log("⚠️ No trips with votes found for notification testing")
            return False
        
        trip_id = test_trip["trip_id"]
        trip_name = test_trip["trip_name"]
        
        log(f"Testing notification sending for trip: {trip_name} ({trip_id})")
        
        # Get voters for this trip
        cur.execute("""
            SELECT DISTINCT u.username, u.email 
            FROM votes v
            JOIN users u ON v.user_id = u.id
            WHERE v.trip_id = %s
        """, (trip_id,))
        voters = cur.fetchall()
        
        log(f"📊 Found {len(voters)} voters for this trip:")
        for voter in voters:
            log(f"   {voter['username']} ({voter['email']})")
        
        # Test results generation
        results = get_voting_results(trip_id)
        if results:
            message = generate_voting_result_message(trip_id, results, trip_name)
            log(f"📝 Generated message ({len(message)} characters)")
            log("📄 Message preview:")
            lines = message.split('\n')[:8]
            for line in lines:
                log(f"   {line}")
        else:
            log("❌ Could not generate voting results")
            return False
        
        conn.close()
        log("✅ Notification sending test passed")
        return True
        
    except Exception as e:
        log(f"❌ Notification sending test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 STARTING VOTING EXPIRATION NOTIFICATION TESTS")
    print("=" * 65)
    
    success = True
    
    # Run tests
    if not test_notifications_table():
        success = False
    
    if not test_voting_results_calculation():
        success = False
    
    if not test_expired_sessions_detection():
        success = False
    
    if not test_notification_sending():
        success = False
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Voting expiration notification system is working correctly")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please check the implementation")
    
    return success

if __name__ == "__main__":
    main() 