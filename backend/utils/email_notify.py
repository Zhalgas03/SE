# utils/email_notify.py
import smtplib, ssl, os, re, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from db import get_db_connection
from psycopg2.extras import RealDictCursor

# --- helpers ---
def _get_sender_tuple(override_sender: str | None = None):
    """
    Возвращает (display_from, login_email, password):
      display_from — то, что увидит получатель (может быть 'Name <addr@...>')
      login_email  — чистый логин (EMAIL_SENDER или адрес из display_from)
      password     — EMAIL_PASSWORD (app password), пробелы убираем на всякий случай
    """
    display_from = override_sender or os.getenv("EMAIL_FROM") or os.getenv("EMAIL_SENDER")
    if not display_from:
        raise RuntimeError("EMAIL_FROM/EMAIL_SENDER is not configured")

    login_email = os.getenv("EMAIL_SENDER")
    if not login_email:
        m = re.search(r"<([^>]+)>", display_from)
        login_email = m.group(1) if m else display_from

    password = (os.getenv("EMAIL_PASSWORD") or "").replace(" ", "")
    if not password:
        raise RuntimeError("EMAIL_PASSWORD is not configured")

    return display_from, login_email, password

def _smtp_send(to_email: str, subject: str, html: str | None, text: str | None, sender: str | None = None) -> bool:
    display_from, login_email, password = _get_sender_tuple(sender)
    msg = MIMEMultipart("alternative")
    msg["From"] = display_from
    msg["To"] = to_email
    msg["Subject"] = subject
    if text:
        msg.attach(MIMEText(text, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(login_email, password)
        server.sendmail(login_email, [to_email], msg.as_string())
    return True

# --- public API ---

def send_email_to_address(to_email: str = None, subject: str = "", html: str | None = None,
                          text: str | None = None, sender: str | None = None, **kwargs) -> bool:
    """Прямая отправка на e-mail (Weekly, маркетинг). БД не трогаем. Поддержка html+plain."""
    if not to_email:
        to_email = kwargs.get("to")  # совместимость со старым вызовом
    if not to_email:
        raise ValueError("to_email is required")
    if not (html or text):
        text = "(empty message)"
    return _smtp_send(to_email, subject, html, text, sender)

def generate_2fa_code() -> str:
    import random
    return str(random.randint(100000, 999999))

def send_email_notification(username: str, subject: str, message: str) -> bool:
    """
    Внутреннее уведомление по username (как у тебя было). Берём email из БД и шлём plain.
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT email FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
        if not row or not row.get("email"):
            print(f"[EMAIL ERROR] User '{username}' not found or missing email")
            return False
        return _smtp_send(row["email"], subject, html=None, text=message, sender=None)
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False
