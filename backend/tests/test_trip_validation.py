#!/usr/bin/env python3
"""
Simple test to verify trip validation in voting endpoints.
This test checks the database directly to understand the issue.
"""

from db import get_db_connection
from psycopg2.extras import RealDictCursor

def test_trip_existence():
    """Test if trips exist in the database"""
    print("🔍 Testing trip existence in database...")
    
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if trips table exists and has data
                cur.execute("SELECT COUNT(*) as count FROM trips")
                result = cur.fetchone()
                total_trips = result["count"] if result else 0
                print(f"📊 Total trips in database: {total_trips}")
                
                # Get some sample trip IDs
                cur.execute("SELECT id, name FROM trips LIMIT 5")
                trips = cur.fetchall()
                
                if trips:
                    print("📋 Sample trips:")
                    for trip in trips:
                        print(f"  - Trip {trip['id']}: {trip['name']}")
                else:
                    print("❌ No trips found in database")
                
                # Test specific trip IDs (using actual UUIDs from the database)
                if trips:
                    test_trip_ids = [trips[0]['id'], trips[1]['id'] if len(trips) > 1 else trips[0]['id'], "non-existent-uuid"]
                    for trip_id in test_trip_ids:
                        cur.execute("SELECT id, name FROM trips WHERE id = %s", (trip_id,))
                        trip = cur.fetchone()
                        if trip:
                            print(f"✅ Trip {trip_id} exists: {trip['name']}")
                        else:
                            print(f"❌ Trip {trip_id} does not exist")
                else:
                    print("❌ No trips available for testing")
                        
    except Exception as e:
        print(f"❌ Database error: {e}")

def test_voting_tables():
    """Test if voting-related tables exist"""
    print("\n🗳️ Testing voting tables...")
    
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check votes table
                cur.execute("SELECT COUNT(*) as count FROM votes")
                result = cur.fetchone()
                total_votes = result["count"] if result else 0
                print(f"📊 Total votes in database: {total_votes}")
                
                # Check voting_rules table
                cur.execute("SELECT COUNT(*) as count FROM voting_rules")
                result = cur.fetchone()
                total_rules = result["count"] if result else 0
                print(f"📊 Total voting rules in database: {total_rules}")
                
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Trip Validation and Database State")
    print("=" * 50)
    
    test_trip_existence()
    test_voting_tables()
    
    print("\n✅ Testing complete!") 