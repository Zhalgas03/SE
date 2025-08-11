# utils/email_notify.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from db import get_db_connection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from config import Config
import random


load_dotenv()   

EMAIL_SENDER = Config.EMAIL_SENDER
EMAIL_PASSWORD = Config.EMAIL_PASSWORD


def generate_2fa_code() -> str:
    return str(random.randint(100000, 999999))


def send_email_notification(username: str, subject: str, message: str) -> bool:
    """
    Отправка email-уведомления по username.
    Email берётся из таблицы users.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT email FROM users WHERE username = %s", (username,))
            result = cur.fetchone()

        conn.close()

        if not result or not result["email"]:
            print(f"[EMAIL ERROR] User '{username}' not found or missing email")
            return False

        recipient_email = result["email"]

        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER or ""
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER or "", EMAIL_PASSWORD or ""  )
            server.send_message(msg)

        print(f"[EMAIL] Sent to {recipient_email}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
