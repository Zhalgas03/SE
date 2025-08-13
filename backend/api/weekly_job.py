# api/weekly_job.py
import email
import os, time, datetime as dt
from flask import current_app, render_template_string
from psycopg2 import OperationalError
from db import get_db_connection
from .weekly_generate import generate_weekly_trip
from .weekly_token import encode_weekly_payload
from utils.email_notify import send_email_notification, send_email_to_address  # твоя SMTP-обёртка

EMAIL_TMPL_HTML = """
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f7fb;padding:24px 0;">
  <tr>
    <td align="center">
      <table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:14px;padding:28px;font-family:Arial,Helvetica,sans-serif;color:#111;">
        <tr><td style="font-size:12px;color:#6b7280;">Trip of the Week · {{ week_label }}</td></tr>
        <tr><td style="padding-top:8px;font-size:26px;font-weight:800;">{{ offer.summary.destination }}</td></tr>
        <tr><td style="padding-top:4px;font-size:14px;color:#6b7280;">{{ offer.meta.duration_days }} days</td></tr>
        <tr><td style="padding-top:10px;font-size:16px;line-height:1.45;color:#374151;">{{ offer.summary.teaser }}</td></tr>

        <tr>
          <td style="padding-top:18px;">
            <a href="{{ preview_url }}"
               style="display:inline-block;background:#111827;color:#fff;text-decoration:none;padding:12px 18px;border-radius:10px;font-weight:700;">
              View trip
            </a>
          </td>
        </tr>

        <tr>
          <td style="padding-top:10px;">
            <a href="{{ preview_url }}" style="font-size:12px;color:#6b7280;">or view online</a>
          </td>
        </tr>
      </table>

      <table width="620" cellpadding="0" cellspacing="0" style="padding:10px 28px 0 28px;font-family:Arial,Helvetica,sans-serif;">
        <tr>
          <td style="font-size:12px;color:#9ca3af;">
            You receive this because you enabled “Trip of the Week”.
            <a href="{{ front_origin }}/account" style="color:#9ca3af;">Turn off weekly emails</a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
"""



def _build_offer_links():
    offer = generate_weekly_trip()

    token = encode_weekly_payload(
        offer,
        current_app.config["JWT_SECRET_KEY"],
        exp_days=14
    )

    base_url     = current_app.config.get("BASE_URL", "http://localhost:5001")
    front_origin = current_app.config.get("FRONT_ORIGIN", "http://localhost:3000")

    preview_url = (
        f"{base_url}/weekly/preview"
        f"?t={token}&utm_source=email&utm_medium=weekly&utm_campaign=trip_of_the_week&a=fav"
    )
    week_label = dt.date.today().strftime("W%V %Y")

    subject = f"Trip of the Week: {offer['summary']['destination']} — {offer['meta']['duration_days']} days"

    html = render_template_string(
        EMAIL_TMPL_HTML,
        week_label=week_label,
        offer=offer,
        preview_url=preview_url,
        base_url=base_url,
        front_origin=front_origin,   # <-- добавили
    )

    text = (
        f"Trip of the Week · {week_label}\n"
        f"{offer['summary']['destination']} — {offer['meta']['duration_days']} days\n\n"
        f"{offer['summary']['teaser']}\n\n"
        f"View trip: {preview_url}\n"
        f"Turn off weekly emails: {front_origin}/account\n"   # <-- заменили
    )

    return offer, subject, html, text, preview_url, week_label


def _select_recipients():
    emails = []
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT email
                FROM users
                WHERE role='premium' AND weekly_trip_opt_in=true AND email IS NOT NULL
            """)
            fetched = cur.fetchall() or []
            for r in fetched:
                # RealDictCursor -> dict, обычный -> tuple
                emails.append(r["email"] if isinstance(r, dict) else r[0])
    except OperationalError as e:
        current_app.logger.error(f"[WEEKLY] DB connect failed: {e}")
    except Exception as e:
        current_app.logger.error(f"[WEEKLY] recipients query failed: {e}")

    # DEV fallback, если никого не нашли
    if not emails:
        dev = os.getenv("DEV_TEST_EMAIL")
        if dev:
            current_app.logger.warning(f"[WEEKLY] using DEV_TEST_EMAIL={dev}")
            emails = [dev]

    return emails

def _send_email(to: str, subject: str, html: str, text: str, sender: str | None):
    """
    Обёртка под разные сигнатуры send_email_notification.
    Пытаемся несколько вариантов, чтобы не падать на несовпадении параметров.
    """
    try:
        return send_email_notification(to=to, subject=subject, html=html, text=text, sender=sender)
    except TypeError:
        try:
            return send_email_notification(to, subject, html, text, sender)
        except TypeError:
            try:
                # минималка: только текст
                return send_email_notification(to, subject, text)
            except Exception:
                raise

def run_weekly_dry_run(app):
    with app.app_context():
        offer, subject, html, text, preview_url, week_label = _build_offer_links()
        recips = _select_recipients()
        return {"ok": True, "mode": "dry", "recipients": len(recips), "preview_url": preview_url, "subject": subject}

def run_weekly_dispatch(app, only_email: str | None = None):
    with app.app_context():
        try:
            offer, subject, html, text, preview_url, week_label = _build_offer_links()
        except Exception as e:
            return {"ok": False, "error": f"generation failed: {e}"}

        recipients = [only_email] if only_email else _select_recipients()
        if not recipients:
            return {"ok": True, "mode": "run", "recipients": 0, "sent": 0, "failed": 0, "preview_url": preview_url}

        sender = current_app.config.get("EMAIL_FROM")
        batch_size = int(os.getenv("WEEKLY_SMTP_BATCH_SIZE", "200"))
        sleep_ms = int(os.getenv("WEEKLY_SMTP_SLEEP_MS", "200"))
        sent = failed = 0

        for i, email in enumerate(recipients, 1):
            try:
                send_email_to_address(to_email=email, subject=subject, html=html, text=text, sender=sender)
                sent += 1
            except Exception as e:
                failed += 1
                print(f"[WEEKLY] send failed to {email}: {e}")
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
            if batch_size and i % batch_size == 0:
                print(f"[WEEKLY] throttle checkpoint: {i}")

        return {"ok": True, "mode": "run", "recipients": len(recipients), "sent": sent, "failed": failed, "preview_url": preview_url}
