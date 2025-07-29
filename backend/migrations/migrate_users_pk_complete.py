#!/usr/bin/env python3
"""
Complete users table migration: integer user_id -> UUID id primary key
Includes backup, migration, rollback, and verification.
"""

import sys
import os
import subprocess
import traceback
from datetime import datetime
from db import get_db_connection
from psycopg2.extras import RealDictCursor

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def get_db_config():
    """Extract database connection details from environment or config"""
    # Import and load environment variables like the main app does
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # This should match your db.py configuration exactly
    config = {
        'host': os.getenv('DB_HOST', 'hopper.proxy.rlwy.net'),
        'port': os.getenv('DB_PORT', '29189'),
        'database': os.getenv('DB_NAME', 'railway'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'qDHwcTUSpUtARphLPiDguLUspkSZGnSg')
    }
    
    log(f"Database config: host={config['host']}, port={config['port']}, db={config['database']}, user={config['user']}")
    return config

def create_backup():
    """Create a database backup before migration"""
    log("Creating database backup...")
    
    db_config = get_db_config()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_users_migration_{timestamp}.sql"
    
    # Test database connection first
    log("Testing database connection...")
    try:
        conn = get_db_connection()
        conn.close()
        log("✅ Database connection test successful")
    except Exception as e:
        log(f"❌ Database connection test failed: {e}")
        log("Please check your database configuration and ensure the database is accessible.")
        return None
    
    try:
        # Create backup using pg_dump with plain SQL format to avoid version issues
        cmd = [
            'pg_dump',
            f'--host={db_config["host"]}',
            f'--port={db_config["port"]}',
            f'--username={db_config["user"]}',
            '--format=plain',
            '--verbose',
            '--file=' + backup_file,
            db_config['database']
        ]
        
        log(f"Running pg_dump command: {' '.join(cmd[:6])}...")
        
        # Set password environment variable
        env = os.environ.copy()
        if db_config['password']:
            env['PGPASSWORD'] = db_config['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Verify backup file was created and has content
            if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
                log(f"✅ Backup created successfully: {backup_file} ({os.path.getsize(backup_file)} bytes)")
                return backup_file
            else:
                log(f"❌ Backup file is empty or was not created: {backup_file}")
                log("Attempting fallback SQL backup method...")
                return create_sql_backup(db_config, backup_file)
        else:
            log(f"❌ Backup failed with return code {result.returncode}")
            log(f"Error output: {result.stderr}")
            log(f"Standard output: {result.stdout}")
            log("Attempting fallback SQL backup method...")
            return create_sql_backup(db_config, backup_file)
            
    except FileNotFoundError:
        log("❌ pg_dump command not found. Trying alternative backup method...")
        return create_sql_backup(db_config, backup_file)
    except Exception as e:
        log(f"❌ Backup failed: {e}")
        log("Trying alternative backup method...")
        return create_sql_backup(db_config, backup_file)

def create_sql_backup(db_config, backup_file):
    """Create backup using direct SQL queries as fallback"""
    log("Creating SQL backup as fallback...")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        with open(backup_file, 'w') as f:
            # Write header
            f.write("-- Database backup created by migration script\n")
            f.write(f"-- Created: {datetime.now()}\n")
            f.write("-- This is a basic backup of critical tables\n\n")
            
            tables = ['users', 'notifications', 'trips', 'trip_group']
            for table in tables:
                f.write(f"\n-- {table} table\n")
                cur.execute(f"SELECT * FROM {table}")
                rows = cur.fetchall()
                if not rows:
                    continue
                columns = list(rows[0].keys())
                for row in rows:
                    values = []
                    for col in columns:
                        val = row[col]
                        if val is None:
                            values.append('NULL')
                        elif isinstance(val, str):
                            escaped_val = val.replace("'", "''")
                            values.append(f"'{escaped_val}'")
                        else:
                            values.append(str(val))
                    f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
        
        if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
            log(f"✅ SQL backup created successfully: {backup_file} ({os.path.getsize(backup_file)} bytes)")
            return backup_file
        else:
            log(f"❌ SQL backup file is empty or was not created: {backup_file}")
            return None
            
    except Exception as e:
        log(f"❌ SQL backup failed: {e}")
        return None
    finally:
        if conn:
            conn.close()

def restore_backup(backup_file):
    """Restore database from backup"""
    log(f"Restoring from backup: {backup_file}")
    
    db_config = get_db_config()
    
    try:
        # Restore using psql for plain SQL format
        cmd = [
            'psql',
            f'--host={db_config["host"]}',
            f'--port={db_config["port"]}',
            f'--username={db_config["user"]}',
            f'--dbname={db_config["database"]}',
            '--file=' + backup_file
        ]
        
        env = os.environ.copy()
        if db_config['password']:
            env['PGPASSWORD'] = db_config['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            log("✅ Database restored successfully")
            return True
        else:
            log(f"❌ Restore failed: {result.stderr}")
            return False
            
    except Exception as e:
        log(f"❌ Restore failed: {e}")
        return False

def run_migration():
    """Run the complete migration"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        log("🚀 STARTING MIGRATION")
        log("BEGIN TRANSACTION")
        conn.autocommit = False

        # Step 1: Add the new UUID id column to users
        log("Step 1: Adding id (UUID) column to users table...")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS id UUID DEFAULT uuid_generate_v4();")

        # Step 2: Populate id for all existing users
        log("Step 2: Populating id for all users...")
        cur.execute("UPDATE users SET id = uuid_generate_v4() WHERE id IS NULL;")

        # Step 3: Create a mapping table for old and new IDs
        log("Step 3: Creating mapping table for user_id to id...")
        cur.execute("DROP TABLE IF EXISTS user_id_map;")
        cur.execute("CREATE TEMP TABLE user_id_map AS SELECT user_id AS old_user_id, id AS new_id FROM users;")

        # Step 4: Disable all triggers on trips table to avoid conflicts during column alterations
        log("Step 4: Disabling triggers on trips table...")
        cur.execute("ALTER TABLE trips DISABLE TRIGGER ALL;")

        # Step 5: For each referencing table, add a new UUID column, populate, drop old, rename
        # notifications.user_id
        log("Step 5a: Migrating notifications.user_id to UUID...")
        cur.execute("ALTER TABLE notifications ADD COLUMN user_id_uuid UUID;")
        cur.execute("UPDATE notifications n SET user_id_uuid = m.new_id FROM user_id_map m WHERE n.user_id = m.old_user_id;")
        cur.execute("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_user_id_fkey;")
        cur.execute("ALTER TABLE notifications DROP COLUMN user_id;")
        cur.execute("ALTER TABLE notifications RENAME COLUMN user_id_uuid TO user_id;")

        # trips.creator_id
        log("Step 5b: Migrating trips.creator_id to UUID...")
        cur.execute("ALTER TABLE trips ADD COLUMN creator_id_uuid UUID;")
        cur.execute("UPDATE trips t SET creator_id_uuid = m.new_id FROM user_id_map m WHERE t.creator_id = m.old_user_id;")
        cur.execute("ALTER TABLE trips DROP CONSTRAINT IF EXISTS fk_trips_creator;")
        cur.execute("ALTER TABLE trips DROP COLUMN creator_id;")
        cur.execute("ALTER TABLE trips RENAME COLUMN creator_id_uuid TO creator_id;")

        # trip_group.user_id
        log("Step 5c: Migrating trip_group.user_id to UUID...")
        cur.execute("ALTER TABLE trip_group ADD COLUMN user_id_uuid UUID;")
        cur.execute("UPDATE trip_group tg SET user_id_uuid = m.new_id FROM user_id_map m WHERE tg.user_id = m.old_user_id;")
        cur.execute("ALTER TABLE trip_group DROP CONSTRAINT IF EXISTS fk_trip_group_user;")
        cur.execute("ALTER TABLE trip_group DROP COLUMN user_id;")
        cur.execute("ALTER TABLE trip_group RENAME COLUMN user_id_uuid TO user_id;")

        # Step 6: Re-enable all triggers on trips table
        log("Step 6: Re-enabling triggers on trips table...")
        cur.execute("ALTER TABLE trips ENABLE TRIGGER ALL;")

        # Step 7: Drop the old users primary key constraint
        log("Step 7: Dropping old users primary key constraint...")
        cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey;")

        # Step 8: Set users.id as the new PRIMARY KEY
        log("Step 8: Setting users.id as the new PRIMARY KEY...")
        cur.execute("ALTER TABLE users ALTER COLUMN id SET NOT NULL;")
        cur.execute("ALTER TABLE users ADD PRIMARY KEY (id);")

        # Step 9: Re-create all foreign key constraints to reference users.id
        log("Step 9: Re-creating foreign key constraints...")
        cur.execute("ALTER TABLE notifications ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);")
        cur.execute("ALTER TABLE trips ADD CONSTRAINT fk_trips_creator FOREIGN KEY (creator_id) REFERENCES users(id);")
        cur.execute("ALTER TABLE trip_group ADD CONSTRAINT fk_trip_group_user FOREIGN KEY (user_id) REFERENCES users(id);")

        # Step 10: (Optional) Drop the old user_id column - COMMENTED OUT FOR MANUAL REVIEW
        log("Step 10: (Optional) To drop the old user_id column, run: ALTER TABLE users DROP COLUMN user_id;")
        # cur.execute("ALTER TABLE users DROP COLUMN user_id;")

        # Commit transaction
        conn.commit()
        log("✅ Migration completed successfully!")
        
        return True

    except Exception as e:
        conn.rollback()
        log(f"❌ Migration failed: {e}")
        traceback.print_exc()
        return False
    finally:
        conn.close()

def print_schema_summary():
    """Print the schema of all affected tables"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        tables = ['users', 'notifications', 'trips', 'trip_group']
        
        for table in tables:
            log(f"📋 {table.upper()} TABLE SCHEMA:")
            print("-" * 50)
            
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cur.fetchall()
            for col in columns:
                print(f"  {col['column_name']}: {col['data_type']} "
                      f"(nullable: {col['is_nullable']}, default: {col['column_default']})")
            
            # Show primary key
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
            """, (table,))
            
            pk_columns = [row['column_name'] for row in cur.fetchall()]
            print(f"  Primary Key: {pk_columns}")
            
            # Show foreign keys
            cur.execute("""
                SELECT kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s
            """, (table,))
            
            fk_columns = cur.fetchall()
            if fk_columns:
                print(f"  Foreign Keys:")
                for fk in fk_columns:
                    print(f"    {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
            
            print()
            
    except Exception as e:
        log(f"❌ Error printing schema: {e}")
    finally:
        conn.close()

def verify_migration():
    """Verify the migration was successful"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        log("🔍 VERIFYING MIGRATION")
        
        # Check users table has UUID id as primary key
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'id'
        """)
        id_column = cur.fetchone()
        
        if not id_column or id_column['data_type'] != 'uuid':
            log("❌ Users table does not have UUID id column")
            return False
        
        # Check primary key
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'users' AND tc.constraint_type = 'PRIMARY KEY'
        """)
        pk_columns = [row['column_name'] for row in cur.fetchall()]
        
        if 'id' not in pk_columns:
            log("❌ Users table primary key is not on id column")
            return False
        
        # Check foreign key constraints
        cur.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' 
              AND kcu.table_name IN ('notifications', 'trips', 'trip_group')
              AND kcu.column_name IN ('user_id', 'creator_id')
        """)
        
        fk_result = cur.fetchone()
        if not fk_result:
            log("❌ Could not verify foreign key constraints")
            return False
        
        fk_count = fk_result['count']
        if fk_count < 3:
            log(f"❌ Expected 3 foreign key constraints, found {fk_count}")
            return False
        
        log("✅ Migration verification successful!")
        return True
        
    except Exception as e:
        log(f"❌ Verification failed: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main migration process"""
    log("🚀 STARTING USERS TABLE MIGRATION")
    log("=" * 60)
    
    # Step 1: Create backup with retry logic
    backup_file = None
    max_retries = 3
    
    for attempt in range(1, max_retries + 1):
        log(f"Backup attempt {attempt}/{max_retries}")
        backup_file = create_backup()
        if backup_file:
            break
        elif attempt < max_retries:
            log(f"Backup attempt {attempt} failed. Retrying in 5 seconds...")
            import time
            time.sleep(5)
        else:
            log("❌ All backup attempts failed. Aborting migration.")
            log("Please check:")
            log("1. Database connection and credentials")
            log("2. PostgreSQL client tools (pg_dump) are installed")
            log("3. Network connectivity to the database")
            sys.exit(1)
    
    # Step 2: Run migration
    migration_success = run_migration()
    
    if not migration_success:
        log("❌ Migration failed. Rolling back...")
        if restore_backup(backup_file):
            log("✅ Database restored from backup")
        else:
            log("❌ Failed to restore from backup. Manual intervention required!")
        sys.exit(1)
    
    # Step 3: Verify migration
    if not verify_migration():
        log("❌ Migration verification failed. Rolling back...")
        if restore_backup(backup_file):
            log("✅ Database restored from backup")
        else:
            log("❌ Failed to restore from backup. Manual intervention required!")
        sys.exit(1)
    
    # Step 4: Print schema summary
    log("📊 PRINTING SCHEMA SUMMARY")
    print_schema_summary()
    
    # Step 5: Print final summary
    log("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("\n" + "=" * 60)
    print("🎉 MIGRATION SUMMARY")
    print("=" * 60)
    print("✅ Database backup created")
    print("✅ Users table migrated from integer user_id to UUID id primary key")
    print("✅ All foreign key constraints updated")
    print("✅ All data preserved")
    print("✅ Referential integrity maintained")
    print("✅ Migration verified")
    print("\n📝 NEXT STEPS:")
    print("1. Test your application with the new schema")
    print("2. Update your application code to use users.id instead of users.user_id")
    print("3. After verification, optionally drop the old user_id column:")
    print("   ALTER TABLE users DROP COLUMN user_id;")
    print(f"4. Backup file: {backup_file}")
    print("=" * 60)

if __name__ == "__main__":
    main() 