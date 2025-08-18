# routes/stripe_routes.py
import os
import stripe
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from utils.email_notify import send_email_notification

# ====== Stripe setup ======
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe_bp = Blueprint("stripe_bp", __name__, url_prefix="/api/pay")


# ====== Health ping (для быстрой проверки маршрута) ======
@stripe_bp.route("/ping", methods=["POST"])
def stripe_ping():
    print("[Stripe] PING hit")
    return "pong", 200


# ====== Create Checkout Session (one‑time payment $5) ======
@stripe_bp.route("/create-checkout-session", methods=["POST"])
@jwt_required()
def create_checkout_session():
    username = get_jwt_identity()
    print(f"[Stripe] create_checkout_session by user={username}")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",  # разовый платёж
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 500,  # $5.00
                    "product_data": {"name": "TripDVisor Premium Subscription"}
                },
                "quantity": 1
            }],
            # важно: прокинем username, чтобы webhook знал кого апдейтить
            metadata={"username": username},
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel",
        )
        print("[Stripe] checkout_session created:", checkout_session.id)
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        print("[Stripe Error][create_checkout_session]", repr(e))
        return jsonify(error=str(e)), 500


# ====== Webhook ======
@stripe_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    print("[Stripe] webhook hit")
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError as e:
        print("[Stripe] Signature error:", repr(e))
        return "Invalid signature", 400
    except Exception as e:
        print("[Stripe] construct_event error:", repr(e))
        return "Bad request", 400

    et = event.get("type")
    print("[Stripe] event type:", et)

    if et == "checkout.session.completed":
        session = event["data"]["object"]
        # Полезно увидеть, что реально приходит
        try:
            print("[Stripe] session dump:", session)
        except Exception:
            pass

        metadata = session.get("metadata") or {}
        username = metadata.get("username")
        payment_status = session.get("payment_status")
        print(f"[Stripe] username={username!r} payment_status={payment_status!r}")

        if not username:
            print("[Stripe] skip: no username in metadata")
            return "ok", 200
        if payment_status != "paid":
            print("[Stripe] skip: not paid")
            return "ok", 200

        # --- Апдейт БД с логами ---
        try:
            conn = get_db_connection()
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT current_database(), current_user")
                    who = cur.fetchone()
                    print("[DB whoami]", who)

                    cur.execute("""
                        UPDATE users
                           SET is_subscribed = TRUE,
                               role = 'premium'
                         WHERE username = %s
                    """, (username,))
                    print("[DB] rows updated:", cur.rowcount)

                    # Если 0 — значит не нашли такого username
                    if cur.rowcount == 0:
                        print("[DB] No user by username. Trying email field fallback…")
                        cur.execute("""
                            UPDATE users
                               SET is_subscribed = TRUE,
                                   role = 'premium'
                             WHERE email = %s
                        """, (username,))
                        print("[DB] rows updated by email:", cur.rowcount)

            print(f"[Webhook] Subscription activated for: {username}")
        except Exception as e:
            print("[Webhook DB error]", repr(e))
            return "DB error", 500

        # Письмо не должно уронить webhook
        try:
            send_email_notification(
                username=username,
                subject="Subscription Activated",
                message="Thank you for subscribing to TripDVisor Premium! You now have access to exclusive features.",
            )
        except Exception as e:
            print("[Webhook Email warn]", repr(e))

    return "Success", 200
