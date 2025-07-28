# routes/notifications.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from psycopg2.extras import RealDictCursor

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api")

# 🔹 Получить все уведомления текущего пользователя
@notifications_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    username = get_jwt_identity()

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if not user:
                return jsonify(success=False, message="User not found"), 404

            cur.execute("""
                SELECT id, title, message, is_read, created_at
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user["id"],))
            notifications = cur.fetchall()
            return jsonify(success=True, notifications=notifications), 200

    except Exception as e:
        print("❌ Get notifications error:", str(e))
        return jsonify(success=False, message="Server error"), 500


# 🔹 Создать уведомление вручную (для тестов/админки)
@notifications_bp.route("/notifications", methods=["POST"])
@jwt_required()
def create_notification_route():
    username = get_jwt_identity()
    data = request.get_json()
    title = data.get("title", "").strip()
    message = data.get("message", "").strip()

    if not title or not message:
        return jsonify(success=False, message="Title and message are required"), 400

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if not user:
                return jsonify(success=False, message="User not found"), 404

            cur.execute("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (%s, %s, %s)
            """, (user["id"], title, message))
            conn.commit()
            return jsonify(success=True, message="Notification created"), 201

    except Exception as e:
        print("❌ Create notification error:", str(e))
        return jsonify(success=False, message="Server error"), 500


# 🔹 Пометить уведомление как прочитанное
@notifications_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_as_read(notification_id):
    username = get_jwt_identity()

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Получаем user_id
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if not user:
                return jsonify(success=False, message="User not found"), 404

            # Обновляем только своё уведомление
            cur.execute("""
                UPDATE notifications
                SET is_read = TRUE
                WHERE id = %s AND user_id = %s
            """, (notification_id, user["id"]))

            if cur.rowcount == 0:
                return jsonify(success=False, message="Notification not found or not yours"), 404

            conn.commit()
            return jsonify(success=True, message="Notification marked as read"), 200

    except Exception as e:
        print("❌ Mark as read error:", str(e))
        return jsonify(success=False, message="Server error"), 500


# 🔹 Удалить уведомление
@notifications_bp.route("/notifications/<int:notification_id>", methods=["DELETE"])
@jwt_required()
def delete_notification(notification_id):
    username = get_jwt_identity()

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Получаем user_id
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if not user:
                return jsonify(success=False, message="User not found"), 404

            # Удаляем только своё уведомление
            cur.execute("""
                DELETE FROM notifications
                WHERE id = %s AND user_id = %s
            """, (notification_id, user["id"]))

            if cur.rowcount == 0:
                return jsonify(success=False, message="Notification not found or not yours"), 404

            conn.commit()
            return jsonify(success=True, message="Notification deleted"), 200

    except Exception as e:
        print("❌ Delete notification error:", str(e))
        return jsonify(success=False, message="Server error"), 500
