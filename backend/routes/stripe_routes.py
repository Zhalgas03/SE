import stripe
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import Config
import os
from db import get_db_connection


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe_bp = Blueprint("stripe_bp", __name__, url_prefix="/api/pay")

@stripe_bp.route("/create-checkout-session", methods=["POST"])
@jwt_required()
def create_checkout_session():
    username = get_jwt_identity()

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 500,  # $5.00
                    "product_data": {
                        "name": "TripDVisor Premium Subscription"
                    }
                },
                "quantity": 1
            }],
            metadata={"username": username},
            success_url="http://localhost:3000/success",
            cancel_url="http://localhost:3000/cancel",
        )
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        print("[Stripe Error]", e)
        return jsonify(error=str(e)), 500

@stripe_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except stripe.SignatureVerificationError as e:
        print("[Webhook Signature Error]", e)
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        username = session.get("metadata", {}).get("username")

        if username:
            try:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users 
                        SET is_subscribed = TRUE,
                            role = 'premium'
                        WHERE username = %s
                    """, (username,))
                    conn.commit()
                print(f"[Webhook] Subscription activated for: {username}")
            except Exception as e:
                print("[Webhook DB error]", e)
                return "DB error", 500

    return "Success", 200