#!/usr/bin/env python3
"""
Audit users table and ensure proper UUID primary key structure
"""

import uuid
from db import get_db_connection
from psycopg2.extras import RealDictCursor

def audit_users_table():
    """Audit the users table structure and provide migration plan"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("🔍 AUDITING USERS TABLE STRUCTURE")
        print("=" * 50)
        
        # Check if users table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        table_exists = cur.fetchone()['exists']
        print(f"✅ Users table exists: {table_exists}")
        
        if not table_exists:
            print("❌ Users table does not exist. Creating it...")
            create_users_table(cur)
            return
        
        # Get current table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default, 
                   is_identity, identity_generation
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        
        print("\n📋 CURRENT TABLE STRUCTURE:")
        print("-" * 30)
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']} "
                  f"(nullable: {col['is_nullable']}, "
                  f"default: {col['column_default']}, "
                  f"identity: {col['is_identity']})")
        
        # Check for id column
        id_column = None
        for col in columns:
            if col['column_name'] == 'id':
                id_column = col
                break
        
        print(f"\n🔍 ID COLUMN ANALYSIS:")
        print("-" * 30)
        if id_column:
            print(f"✅ ID column exists")
            print(f"   Type: {id_column['data_type']}")
            print(f"   Nullable: {id_column['is_nullable']}")
            print(f"   Default: {id_column['column_default']}")
            print(f"   Identity: {id_column['is_identity']}")
        else:
            print("❌ ID column does not exist")
        
        # Check primary key
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'users' AND tc.constraint_type = 'PRIMARY KEY'
        """)
        pk_columns = [row['column_name'] for row in cur.fetchall()]
        print(f"\n🔑 PRIMARY KEY COLUMNS: {pk_columns}")
        
        # Check for uuid extension
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp'
            )
        """)
        uuid_ext_exists = cur.fetchone()['exists']
        print(f"\n🔧 UUID EXTENSION: {'✅ Available' if uuid_ext_exists else '❌ Not available'}")
        
        # Sample data
        cur.execute("SELECT * FROM users LIMIT 3")
        sample_data = cur.fetchall()
        print(f"\n📊 SAMPLE DATA (first 3 rows):")
        for row in sample_data:
            print(f"  {dict(row)}")
        
        # Generate migration plan
        print(f"\n📝 MIGRATION PLAN:")
        print("-" * 30)
        generate_migration_plan(cur, id_column, pk_columns, uuid_ext_exists, columns)
        
    except Exception as e:
        print(f"❌ Error during audit: {e}")
    finally:
        conn.close()

def create_users_table(cur):
    """Create users table with proper UUID primary key"""
    print("Creating users table with UUID primary key...")
    
    # Ensure uuid extension is available
    cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    
    # Create users table
    cur.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ Users table created successfully")

def generate_migration_plan(cur, id_column, pk_columns, uuid_ext_exists, columns):
    """Generate migration plan based on current state"""
    
    if not uuid_ext_exists:
        print("1. Install UUID extension:")
        print("   CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
    
    if not id_column:
        print("2. Add ID column:")
        print("   ALTER TABLE users ADD COLUMN id UUID DEFAULT uuid_generate_v4();")
        print("   UPDATE users SET id = uuid_generate_v4() WHERE id IS NULL;")
        print("   ALTER TABLE users ALTER COLUMN id SET NOT NULL;")
        
        # Check if there's an existing primary key
        if pk_columns:
            print(f"3. Drop existing primary key on: {pk_columns}")
            print(f"   ALTER TABLE users DROP CONSTRAINT users_pkey;")
        
        print("4. Set ID as primary key:")
        print("   ALTER TABLE users ADD PRIMARY KEY (id);")
        
    elif id_column['data_type'] != 'uuid':
        print("2. Convert ID column to UUID:")
        print("   ALTER TABLE users ALTER COLUMN id TYPE UUID USING id::UUID;")
        print("   ALTER TABLE users ALTER COLUMN id SET DEFAULT uuid_generate_v4();")
        
    elif 'id' not in pk_columns:
        print("2. Set ID as primary key:")
        if pk_columns:
            print(f"   ALTER TABLE users DROP CONSTRAINT users_pkey;")
        print("   ALTER TABLE users ADD PRIMARY KEY (id);")
        
    else:
        print("✅ Users table already has proper UUID primary key structure!")
        
        # Check if default is correct
        if not id_column['column_default'] or 'uuid_generate_v4' not in str(id_column['column_default']):
            print("3. Update default value:")
            print("   ALTER TABLE users ALTER COLUMN id SET DEFAULT uuid_generate_v4();")

def execute_migration():
    """Execute the migration to fix users table"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("\n🚀 EXECUTING MIGRATION")
        print("=" * 50)
        
        # Ensure uuid extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        print("✅ UUID extension ensured")
        
        # Check current state
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'id'
        """)
        id_column = cur.fetchone()
        
        if not id_column:
            print("📝 Adding ID column...")
            cur.execute("ALTER TABLE users ADD COLUMN id UUID DEFAULT uuid_generate_v4()")
            cur.execute("UPDATE users SET id = uuid_generate_v4() WHERE id IS NULL")
            cur.execute("ALTER TABLE users ALTER COLUMN id SET NOT NULL")
            print("✅ ID column added")
            
            # Check existing primary key
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'users' AND tc.constraint_type = 'PRIMARY KEY'
            """)
            pk_columns = [row['column_name'] for row in cur.fetchall()]
            
            if pk_columns and 'id' not in pk_columns:
                print(f"📝 Dropping existing primary key on: {pk_columns}")
                cur.execute("ALTER TABLE users DROP CONSTRAINT users_pkey")
            
            print("📝 Setting ID as primary key...")
            cur.execute("ALTER TABLE users ADD PRIMARY KEY (id)")
            print("✅ ID set as primary key")
            
        else:
            print("📝 ID column exists, checking type...")
            if id_column['data_type'] != 'uuid':
                print("📝 Converting ID to UUID...")
                cur.execute("ALTER TABLE users ALTER COLUMN id TYPE UUID USING id::UUID")
                print("✅ ID converted to UUID")
            
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
                print("📝 Setting ID as primary key...")
                if pk_columns:
                    cur.execute("ALTER TABLE users DROP CONSTRAINT users_pkey")
                cur.execute("ALTER TABLE users ADD PRIMARY KEY (id)")
                print("✅ ID set as primary key")
            
            # Update default if needed
            if not id_column['column_default'] or 'uuid_generate_v4' not in str(id_column['column_default']):
                print("📝 Updating default value...")
                cur.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT uuid_generate_v4()")
                print("✅ Default value updated")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Show final schema
        print("\n📋 FINAL TABLE SCHEMA:")
        print("-" * 30)
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        for col in cur.fetchall():
            print(f"  {col['column_name']}: {col['data_type']} "
                  f"(nullable: {col['is_nullable']}, default: {col['column_default']})")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    audit_users_table()
    
    # Ask user if they want to proceed with migration
    response = input("\n🤔 Do you want to proceed with the migration? (y/N): ")
    if response.lower() in ['y', 'yes']:
        execute_migration()
    else:
        print("Migration cancelled.") 