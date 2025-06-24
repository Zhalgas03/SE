import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    import os
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "hopper.proxy.rlwy.net"),
        port=int(os.getenv("DB_PORT", "29189")),
        database=os.getenv("DB_NAME", "railway"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "qDHwcTUSpUtARphLPiDguLUspkSZGnSg"),
        cursor_factory=RealDictCursor
    )
