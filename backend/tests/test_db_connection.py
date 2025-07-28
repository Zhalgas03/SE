#!/usr/bin/env python3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_db_connection():
    """Test the database connection with detailed error reporting"""
    print("Testing database connection...")
    print(f"Host: {os.getenv('DB_HOST', 'hopper.proxy.rlwy.net')}")
    print(f"Port: {os.getenv('DB_PORT', '29189')}")
    print(f"Database: {os.getenv('DB_NAME', 'railway')}")
    print(f"User: {os.getenv('DB_USER', 'postgres')}")
    print(f"Password: {'*' * len(os.getenv('DB_PASSWORD', 'qDHwcTUSpUtARphLPiDguLUspkSZGnSg'))}")
    
    try:
        # Attempt to connect
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "hopper.proxy.rlwy.net"),
            port=int(os.getenv("DB_PORT", "29189")),
            database=os.getenv("DB_NAME", "railway"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "qDHwcTUSpUtARphLPiDguLUspkSZGnSg"),
            cursor_factory=RealDictCursor
        )
        
        print("✅ Database connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        if version:
            print(f"✅ Database version: {version['version']}")
        
        # Test if we can access the users table
        try:
            cursor.execute("SELECT COUNT(*) as count FROM users;")
            user_count = cursor.fetchone()
            if user_count:
                print(f"✅ Users table accessible. User count: {user_count['count']}")
        except Exception as e:
            print(f"⚠️  Could not access users table: {e}")
        
        cursor.close()
        conn.close()
        print("✅ Connection closed successfully")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("This could be due to:")
        print("- Network connectivity issues")
        print("- Database server is down")
        print("- Incorrect connection parameters")
        print("- Firewall blocking the connection")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_db_connection() 