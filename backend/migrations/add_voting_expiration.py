#!/usr/bin/env python3
"""
Migration: Add voting expiration tracking to voting_rules table
Adds created_at and expires_at columns to track when voting sessions start and end
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def run_migration():
    """Add expiration tracking columns to voting_rules table"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        log("🚀 STARTING VOTING EXPIRATION MIGRATION")
        log("BEGIN TRANSACTION")
        conn.autocommit = False

        # Step 1: Check current voting_rules table structure
        log("Step 1: Checking current voting_rules table structure...")
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'voting_rules' 
            ORDER BY ordinal_position
        """)
        voting_rules_schema = cur.fetchall()
        log("Current voting_rules table schema:")
        for col in voting_rules_schema:
            log(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

        # Step 2: Add created_at column if it doesn't exist
        log("Step 2: Adding created_at column...")
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'voting_rules' AND column_name = 'created_at'
        """)
        if not cur.fetchone():
            log("   Adding created_at column to voting_rules...")
            cur.execute("ALTER TABLE voting_rules ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            log("   ✅ created_at column added")
        else:
            log("   ✅ created_at column already exists")

        # Step 3: Add expires_at column if it doesn't exist
        log("Step 3: Adding expires_at column...")
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'voting_rules' AND column_name = 'expires_at'
        """)
        if not cur.fetchone():
            log("   Adding expires_at column to voting_rules...")
            cur.execute("ALTER TABLE voting_rules ADD COLUMN expires_at TIMESTAMP")
            log("   ✅ expires_at column added")
        else:
            log("   ✅ expires_at column already exists")

        # Step 4: Update existing voting rules with default expiration (24 hours from now)
        log("Step 4: Updating existing voting rules with default expiration...")
        cur.execute("""
            UPDATE voting_rules 
            SET expires_at = created_at + INTERVAL '24 hours'
            WHERE expires_at IS NULL
        """)
        updated_count = cur.rowcount
        log(f"   ✅ Updated {updated_count} existing voting rules with default expiration")

        # Step 5: Verify the migration
        log("Step 5: Verifying migration...")
        cur.execute("""
            SELECT COUNT(*) as count FROM voting_rules 
            WHERE expires_at IS NOT NULL
        """)
        result = cur.fetchone()
        total_rules = result["count"] if result else 0
        log(f"   ✅ Total voting rules with expiration: {total_rules}")

        # Commit the transaction
        conn.commit()
        log("✅ MIGRATION COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        conn.rollback()
        log(f"❌ MIGRATION FAILED: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration() 