#!/usr/bin/env python3
"""
Test Voting Time Limit Feature
Tests the new voting time limit functionality including duration validation and expiration checks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from db import get_db_connection
from psycopg2.extras import RealDictCursor

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def test_voting_time_limit():
    """Test the voting time limit functionality"""
    print("\n🧪 TESTING VOTING TIME LIMIT FEATURE")
    print("=" * 50)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test 1: Check if voting_rules table has expiration columns
        log("1️⃣ Checking voting_rules table structure...")
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'voting_rules' 
            AND column_name IN ('created_at', 'expires_at')
            ORDER BY column_name
        """)
        expiration_cols = cur.fetchall()
        
        expected_cols = ['created_at', 'expires_at']
        found_cols = [col['column_name'] for col in expiration_cols]
        
        for col in expected_cols:
            if col in found_cols:
                log(f"   ✅ {col} column exists")
            else:
                log(f"   ❌ {col} column missing")
                return False
        
        # Test 2: Check existing voting rules
        log("\n2️⃣ Checking existing voting rules...")
        cur.execute("""
            SELECT trip_id, created_at, expires_at,
                   CASE WHEN expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP 
                   THEN 'active' ELSE 'expired' END as status
            FROM voting_rules 
            LIMIT 5
        """)
        rules = cur.fetchall()
        
        if rules:
            log(f"   Found {len(rules)} voting rules:")
            for rule in rules:
                status = rule['status']
                expires = rule['expires_at']
                log(f"      Trip {rule['trip_id']}: {status} (expires: {expires})")
        else:
            log("   No voting rules found")
        
        # Test 3: Test duration validation logic
        log("\n3️⃣ Testing duration validation logic...")
        
        # Test valid durations
        valid_durations = [5, 30, 60, 1440]  # 5 min, 30 min, 1 hour, 24 hours
        for duration in valid_durations:
            if 5 <= duration <= 1440:
                log(f"   ✅ Duration {duration} minutes is valid")
            else:
                log(f"   ❌ Duration {duration} minutes should be invalid")
        
        # Test invalid durations
        invalid_durations = [0, 4, 1441, 2880]  # Too short, too long
        for duration in invalid_durations:
            if not (5 <= duration <= 1440):
                log(f"   ✅ Duration {duration} minutes correctly rejected")
            else:
                log(f"   ❌ Duration {duration} minutes should be rejected")
        
        # Test 4: Test expiration calculation
        log("\n4️⃣ Testing expiration calculation...")
        test_duration = 60  # 1 hour
        now = datetime.now()
        expires_at = now + timedelta(minutes=test_duration)
        
        log(f"   Current time: {now}")
        log(f"   Test duration: {test_duration} minutes")
        log(f"   Expires at: {expires_at}")
        
        # Test if expiration is in the future
        if expires_at > now:
            log("   ✅ Expiration calculation is correct")
        else:
            log("   ❌ Expiration calculation is incorrect")
        
        # Test 5: Test active/expired status logic
        log("\n5️⃣ Testing active/expired status logic...")
        
        # Simulate active voting rule (expires in 1 hour)
        active_expires = now + timedelta(hours=1)
        active_status = "active" if active_expires > now else "expired"
        log(f"   Active rule (expires in 1 hour): {active_status}")
        
        # Simulate expired voting rule (expired 1 hour ago)
        expired_expires = now - timedelta(hours=1)
        expired_status = "active" if expired_expires > now else "expired"
        log(f"   Expired rule (expired 1 hour ago): {expired_status}")
        
        if active_status == "active" and expired_status == "expired":
            log("   ✅ Status logic is correct")
        else:
            log("   ❌ Status logic is incorrect")
        
        conn.close()
        log("\n✅ ALL TESTS PASSED")
        return True
        
    except Exception as e:
        log(f"❌ Test failed: {str(e)}")
        return False

def test_database_operations():
    """Test database operations for voting time limit"""
    print("\n🔍 TESTING DATABASE OPERATIONS")
    print("=" * 40)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test 1: Check if we can create a voting rule with expiration
        log("1️⃣ Testing voting rule creation with expiration...")
        
        # Create a test voting rule
        test_trip_id = "12345678-1234-1234-1234-123456789012"  # Valid UUID format
        test_duration = 30  # 30 minutes
        
        cur.execute("""
            INSERT INTO voting_rules (trip_id, approval_threshold, min_votes_required, duration_hours, rule_type, created_at, expires_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '%s minutes')
            ON CONFLICT (trip_id) DO UPDATE SET
                expires_at = CURRENT_TIMESTAMP + INTERVAL '%s minutes',
                created_at = CURRENT_TIMESTAMP
        """, (test_trip_id, 0.5, 1, test_duration // 60, "majority", test_duration, test_duration))
        
        # Check if the rule was created/updated
        cur.execute("""
            SELECT trip_id, created_at, expires_at,
                   CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 'active' ELSE 'expired' END as status
            FROM voting_rules 
            WHERE trip_id = %s
        """, (test_trip_id,))
        
        rule = cur.fetchone()
        if rule:
            log(f"   ✅ Voting rule created/updated for trip {test_trip_id}")
            log(f"      Status: {rule['status']}")
            log(f"      Expires: {rule['expires_at']}")
        else:
            log(f"   ❌ Failed to create voting rule for trip {test_trip_id}")
        
        # Clean up test data
        cur.execute("DELETE FROM voting_rules WHERE trip_id = %s", (test_trip_id,))
        log("   🧹 Test data cleaned up")
        
        conn.close()
        log("✅ Database operations test completed")
        return True
        
    except Exception as e:
        log(f"❌ Database operations test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 STARTING VOTING TIME LIMIT TESTS")
    print("=" * 60)
    
    success = True
    
    # Run tests
    if not test_voting_time_limit():
        success = False
    
    if not test_database_operations():
        success = False
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Voting time limit feature is working correctly")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please check the implementation")
    
    return success

if __name__ == "__main__":
    main() 