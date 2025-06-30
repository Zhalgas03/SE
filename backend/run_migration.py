#!/usr/bin/env python3
"""
Migration Runner for Trip Management System

This script safely executes the SQL migration to create trip-related tables.
It includes proper error handling, logging, and validation.

Usage:
    python run_migration.py

Dependencies:
    - psycopg2 (for PostgreSQL connection)
    - python-dotenv (for environment variables)
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Create database connection using environment variables"""
    try:
        # Get database connection parameters from environment
        db_url = os.getenv('DATABASE_URL')
        
        if db_url:
            # Parse DATABASE_URL format: postgresql://user:password@host:port/database
            conn = psycopg2.connect(db_url)
        else:
            # Fallback to individual environment variables
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'postgres'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', '')
            )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def check_table_exists(conn, table_name):
    """Check if a table exists in the database"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error checking if table {table_name} exists: {e}")
        return False

def read_migration_file():
    """Read the migration SQL file"""
    migration_file = os.path.join(os.path.dirname(__file__), 'migrations', '002_fix_schema_mismatch.sql')
    
    if not os.path.exists(migration_file):
        raise FileNotFoundError(f"Migration file not found: {migration_file}")
    
    with open(migration_file, 'r') as f:
        return f.read()

def execute_migration():
    """Execute the migration with proper error handling"""
    start_time = datetime.now()
    logger.info("Starting migration execution...")
    
    try:
        # Connect to database
        conn = get_database_connection()
        logger.info("Successfully connected to database")
        
        # Check current state
        existing_tables = []
        for table in ['trips', 'voting_rules', 'votes', 'trip_group']:
            if check_table_exists(conn, table):
                existing_tables.append(table)
        
        if existing_tables:
            logger.warning(f"Found existing tables: {', '.join(existing_tables)}")
            logger.info("Migration will skip existing tables (safe additive migration)")
        
        # Read and execute migration
        migration_sql = read_migration_file()
        logger.info("Migration SQL loaded successfully")
        
        with conn.cursor() as cursor:
            logger.info("Executing migration SQL...")
            cursor.execute(migration_sql)
            logger.info("Migration SQL executed successfully")
        
        # Verify migration results
        logger.info("Verifying migration results...")
        created_tables = []
        for table in ['trips', 'voting_rules', 'votes', 'trip_group']:
            if check_table_exists(conn, table):
                created_tables.append(table)
        
        logger.info(f"Successfully created/verified tables: {', '.join(created_tables)}")
        
        # Check for enum types
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT typname FROM pg_type 
                WHERE typname IN ('trip_status', 'vote_type', 'user_role')
                AND typtype = 'e';
            """)
            enums = [row[0] for row in cursor.fetchall()]
            logger.info(f"Created enum types: {', '.join(enums)}")
        
        # Check for functions
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT proname FROM pg_proc 
                WHERE proname IN ('get_trip_voting_status', 'can_user_vote_on_trip', 'update_updated_at_column');
            """)
            functions = [row[0] for row in cursor.fetchall()]
            logger.info(f"Created functions: {', '.join(functions)}")
        
        conn.close()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"Migration completed successfully in {duration}")
        logger.info("All trip management tables, enums, and functions are ready!")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.error("Please check the migration.log file for details")
        return False

def main():
    """Main function to run the migration"""
    logger.info("=" * 60)
    logger.info("Trip Management System - Migration Runner")
    logger.info("=" * 60)
    
    # Check environment
    required_vars = ['DATABASE_URL'] if os.getenv('DATABASE_URL') else ['DB_HOST', 'DB_NAME', 'DB_USER']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set DATABASE_URL or individual DB_* variables")
        sys.exit(1)
    
    # Execute migration
    success = execute_migration()
    
    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 