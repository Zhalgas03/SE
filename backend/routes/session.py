# routes/session.py
from flask import Blueprint, jsonify, make_response
import uuid
from utils.logging import log_guest_action

session_bp = Blueprint("session", __name__, url_prefix="/api/session")

@session_bp.route("/init", methods=["GET"])
def init_guest_session():
    session_token = str(uuid.uuid4())

    log_guest_action(session_token, "init_session")


    response = make_response(jsonify(success=True, session_token=session_token))
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,        # ✅ ставь True на проде (HTTPS)
        samesite="Lax",
        max_age=60*60*24*7   # 7 дней
    )

    return response

