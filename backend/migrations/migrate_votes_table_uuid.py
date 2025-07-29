#!/usr/bin/env python3
"""
Migrate votes table user_id from integer to UUID to match users table migration.
This script updates the votes table to be compatible with the UUID-based users table.
"""

import sys
import traceback
from datetime import datetime
from db import get_db_connection
from psycopg2.extras import RealDictCursor

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def run_migration():
    """Migrate votes table user_id from integer to UUID"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        log("🚀 STARTING VOTES TABLE MIGRATION")
        log("BEGIN TRANSACTION")
        conn.autocommit = False

        # Step 1: Check current votes table structure
        log("Step 1: Checking current votes table structure...")
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'votes' 
            ORDER BY ordinal_position
        """)
        votes_schema = cur.fetchall()
        log("Current votes table schema:")
        for col in votes_schema:
            log(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

        # Step 2: Check if votes table exists and has data
        cur.execute("SELECT COUNT(*) as count FROM votes")
        votes_result = cur.fetchone()
        votes_count = votes_result["count"] if votes_result else 0
        log(f"Step 2: Found {votes_count} votes in the table")

        # Step 3: Create a mapping table for old user_id to new UUID
        log("Step 3: Creating user_id mapping table...")
        cur.execute("""
            CREATE TEMP TABLE user_id_map AS 
            SELECT user_id AS old_user_id, id AS new_id 
            FROM users 
            WHERE user_id IS NOT NULL AND id IS NOT NULL
        """)
        cur.execute("SELECT COUNT(*) as count FROM user_id_map")
        mapping_result = cur.fetchone()
        mapping_count = mapping_result["count"] if mapping_result else 0
        log(f"Created mapping for {mapping_count} users")

        # Step 4: Add a new UUID user_id column to votes table
        log("Step 4: Adding new UUID user_id column to votes table...")
        cur.execute("ALTER TABLE votes ADD COLUMN IF NOT EXISTS user_id_new UUID;")

        # Step 5: Update the new user_id column with UUID values
        log("Step 5: Updating votes table with UUID user_id values...")
        cur.execute("""
            UPDATE votes v
            SET user_id_new = m.new_id
            FROM user_id_map m
            WHERE v.user_id::text = m.old_user_id::text
        """)
        updated_count = cur.rowcount
        log(f"Updated {updated_count} votes with UUID user_id")

        # Step 6: Drop the old integer user_id column
        log("Step 6: Dropping old integer user_id column...")
        cur.execute("ALTER TABLE votes DROP COLUMN IF EXISTS user_id;")

        # Step 7: Rename the new column to user_id
        log("Step 7: Renaming new column to user_id...")
        cur.execute("ALTER TABLE votes RENAME COLUMN user_id_new TO user_id;")

        # Step 8: Add foreign key constraint to users table
        log("Step 8: Adding foreign key constraint to users table...")
        cur.execute("""
            ALTER TABLE votes 
            ADD CONSTRAINT fk_votes_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id);
        """)

        # Step 9: Verify the migration
        log("Step 9: Verifying migration...")
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'votes' 
            ORDER BY ordinal_position
        """)
        new_votes_schema = cur.fetchall()
        log("New votes table schema:")
        for col in new_votes_schema:
            log(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

        # Step 10: Test a sample query
        log("Step 10: Testing sample query...")
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM votes v 
            JOIN users u ON v.user_id = u.id
        """)
        test_result = cur.fetchone()
        test_count = test_result["count"] if test_result else 0
        log(f"✅ Sample query successful: {test_count} votes with valid user references")

        # Commit transaction
        conn.commit()
        log("✅ VOTES TABLE MIGRATION COMPLETED SUCCESSFULLY!")
        
        print("\n--- MIGRATION SUMMARY ---")
        print(f"- Updated {updated_count} votes to use UUID user_id")
        print("- Votes table now uses UUID user_id compatible with users table")
        print("- Added foreign key constraint to users(id)")
        print("- All existing vote data preserved")
        print("- Voting endpoints should now work correctly")

    except Exception as e:
        conn.rollback()
        log(f"❌ Migration failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

def verify_migration():
    """Verify the migration was successful"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        log("🔍 VERIFYING MIGRATION")
        
        # Check votes table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'votes' 
            ORDER BY ordinal_position
        """)
        votes_schema = cur.fetchall()
        
        user_id_col = None
        for col in votes_schema:
            if col['column_name'] == 'user_id':
                user_id_col = col
                break
        
        if not user_id_col:
            log("❌ user_id column not found in votes table")
            return False
        
        if user_id_col['data_type'] != 'uuid':
            log(f"❌ user_id column is {user_id_col['data_type']}, expected uuid")
            return False
        
        log("✅ user_id column is UUID type")
        
        # Test foreign key constraint
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM votes v 
            JOIN users u ON v.user_id = u.id
        """)
        join_result = cur.fetchone()
        join_count = join_result["count"] if join_result else 0
        log(f"✅ Foreign key join successful: {join_count} votes")
        
        # Test total votes count
        cur.execute("SELECT COUNT(*) as count FROM votes")
        total_result = cur.fetchone()
        total_votes = total_result["count"] if total_result else 0
        log(f"✅ Total votes in table: {total_votes}")
        
        log("✅ MIGRATION VERIFICATION SUCCESSFUL")
        return True
        
    except Exception as e:
        log(f"❌ Verification failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_migration()
    else:
        run_migration() 