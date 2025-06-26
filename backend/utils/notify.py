# utils/notify.py

from db import get_db_connection

def create_notification(user_id: int, title: str, message: str):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (%s, %s, %s)
            """, (user_id, title, message))
            conn.commit()
    except Exception as e:
        print("❌ create_notification error:", str(e))
