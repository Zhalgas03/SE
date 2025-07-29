#!/usr/bin/env python3
"""
Check all table schemas and identify any issues
"""

from db import get_db_connection
from psycopg2.extras import RealDictCursor

def check_schemas():
    """Check all table schemas"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    tables = ['users', 'trips', 'votes', 'notifications', 'trip_group']
    
    for table in tables:
        print(f"\n{table.upper()} TABLE:")
        try:
            cur.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position
            """)
            result = cur.fetchall()
            for row in result:
                print(f"  {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']}, default: {row['column_default']})")
        except Exception as e:
            print(f"  Error checking {table}: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_schemas() 