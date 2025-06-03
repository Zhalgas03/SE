# trip/models.py

from db import get_db_connection

def create_trip(name, creator_email, date_start, date_end):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (creator_email,))
            user = cur.fetchone()
            if not user:
                raise Exception("User not found")
            user_id = user["id"]

            cur.execute(
                "INSERT INTO trips (name, creator_id, date_start, date_end) VALUES (%s, %s, %s, %s) RETURNING id",
                (name, user_id, date_start, date_end)
            )
            trip_id = cur.fetchone()["id"]
            return trip_id

def get_trip_by_id(trip_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM trips WHERE id = %s", (trip_id,))
        return cur.fetchone()

def update_trip(trip_id, email, name, date_start, date_end):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                return False

            cur.execute(
                "UPDATE trips SET name=%s, date_start=%s, date_end=%s WHERE id=%s AND creator_id=%s",
                (name, date_start, date_end, trip_id, user["id"])
            )
            return cur.rowcount > 0

def delete_trip(trip_id, email):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                return False

            cur.execute("DELETE FROM trips WHERE id=%s AND creator_id=%s", (trip_id, user["id"]))
            return cur.rowcount > 0

def list_user_trips(email):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT t.* FROM trips t
            JOIN users u ON t.creator_id = u.id
            WHERE u.email = %s
        """, (email,))
        return cur.fetchall()
