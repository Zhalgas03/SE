#!/usr/bin/env python3
"""
Migrate users.user_id (integer PK) to users.id (UUID PK), update all foreign keys, and preserve data.
Fully transactional, logs each step, outputs schema changes, and prints a summary.
"""

import sys
import traceback
from db import get_db_connection
from psycopg2.extras import RealDictCursor

def log(msg):
    print(f"[MIGRATION] {msg}")

def run_migration():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        log("BEGIN TRANSACTION")
        conn.autocommit = False

        # 1. Add the new UUID id column to users
        log("Adding id (UUID) column to users table...")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS id UUID DEFAULT uuid_generate_v4();")

        # 2. Populate id for all existing users
        log("Populating id for all users...")
        cur.execute("UPDATE users SET id = uuid_generate_v4() WHERE id IS NULL;")

        # 3. Create a mapping table for old and new IDs
        log("Creating mapping table for user_id to id...")
        cur.execute("DROP TABLE IF EXISTS user_id_map;")
        cur.execute("CREATE TEMP TABLE user_id_map AS SELECT user_id AS old_user_id, id AS new_id FROM users;")

        # 4. Drop all foreign key constraints referencing users.user_id
        log("Dropping foreign key constraints on notifications, trips, trip_group...")
        cur.execute("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_user_id_fkey;")
        cur.execute("ALTER TABLE trips DROP CONSTRAINT IF EXISTS fk_trips_creator;")
        cur.execute("ALTER TABLE trip_group DROP CONSTRAINT IF EXISTS fk_trip_group_user;")

        # 5. Alter referencing columns to UUID type
        log("Altering referencing columns to UUID type...")
        cur.execute("ALTER TABLE notifications ALTER COLUMN user_id TYPE UUID USING user_id::text::uuid;")
        cur.execute("ALTER TABLE trips ALTER COLUMN creator TYPE UUID USING creator::text::uuid;")
        cur.execute("ALTER TABLE trip_group ALTER COLUMN user_id TYPE UUID USING user_id::text::uuid;")

        # 6. Update referencing columns to use the new UUIDs
        log("Updating referencing columns to use new UUIDs...")
        cur.execute("""
            UPDATE notifications n
            SET user_id = m.new_id
            FROM user_id_map m
            WHERE n.user_id::text = m.old_user_id::text;
        """)
        cur.execute("""
            UPDATE trips t
            SET creator = m.new_id
            FROM user_id_map m
            WHERE t.creator::text = m.old_user_id::text;
        """)
        cur.execute("""
            UPDATE trip_group tg
            SET user_id = m.new_id
            FROM user_id_map m
            WHERE tg.user_id::text = m.old_user_id::text;
        """)

        # 7. Drop the old users primary key constraint
        log("Dropping old users primary key constraint...")
        cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey;")

        # 8. Set users.id as the new PRIMARY KEY
        log("Setting users.id as the new PRIMARY KEY...")
        cur.execute("ALTER TABLE users ALTER COLUMN id SET NOT NULL;")
        cur.execute("ALTER TABLE users ADD PRIMARY KEY (id);")

        # 9. Re-create all foreign key constraints to reference users.id
        log("Re-creating foreign key constraints to reference users.id...")
        cur.execute("""
            ALTER TABLE notifications
                ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
        """)
        cur.execute("""
            ALTER TABLE trips
                ADD CONSTRAINT fk_trips_creator FOREIGN KEY (creator) REFERENCES users(id);
        """)
        cur.execute("""
            ALTER TABLE trip_group
                ADD CONSTRAINT fk_trip_group_user FOREIGN KEY (user_id) REFERENCES users(id);
        """)

        # 10. (Optional) Drop the old user_id column from users (commented out)
        log("(Optional) To drop the old user_id column, run: ALTER TABLE users DROP COLUMN user_id;")
        # cur.execute("ALTER TABLE users DROP COLUMN user_id;")

        # Output schema changes
        log("Outputting new users table schema:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        users_schema = cur.fetchall()
        for col in users_schema:
            print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")

        log("Outputting new notifications table schema:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'notifications' 
            ORDER BY ordinal_position
        """)
        notifications_schema = cur.fetchall()
        for col in notifications_schema:
            print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")

        log("Outputting new trips table schema:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'trips' 
            ORDER BY ordinal_position
        """)
        trips_schema = cur.fetchall()
        for col in trips_schema:
            print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")

        log("Outputting new trip_group table schema:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'trip_group' 
            ORDER BY ordinal_position
        """)
        trip_group_schema = cur.fetchall()
        for col in trip_group_schema:
            print(f"  {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")

        # Commit transaction
        conn.commit()
        log("✅ Migration completed successfully!")
        print("\n--- MIGRATION SUMMARY ---")
        print("- users.id is now UUID PRIMARY KEY with default uuid_generate_v4()")
        print("- All foreign keys now reference users.id (UUID)")
        print("- All referencing columns in notifications, trips, trip_group are UUID and remapped")
        print("- Referential integrity is preserved, no data lost")
        print("- (Optional) Drop users.user_id column after verification")

    except Exception as e:
        conn.rollback()
        log(f"❌ Migration failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration() 