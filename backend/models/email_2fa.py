import random
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

def generate_2fa_code() -> str:
    return str(random.randint(100000, 999999))

def send_2fa_email(recipient: str, code: str):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    if not sender or not password:
        raise ValueError("EMAIL_SENDER and EMAIL_PASSWORD must be set in environment variables.")

    msg = MIMEText(f"Your verification code is: {code}")
    msg["Subject"] = "Your 2FA Code"
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
