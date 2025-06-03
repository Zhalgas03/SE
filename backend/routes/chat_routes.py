# routes/chat_routes.py
from flask import Blueprint, request, jsonify
from services.system_prompt import SYSTEM_PROMPT
from config import Config
from db import SessionLocal
from models.ai_plan import TripAIPlan
import requests, json

chat_bp = Blueprint("chat", __name__, url_prefix="/api")
chat_history = []

@chat_bp.route("/perplexity-chat", methods=["POST"])
def perplexity_chat():
    global chat_history
    msg = request.json.get("message")

    if not msg:
        return jsonify({"reply": "No input received"}), 400

    if not chat_history:
        chat_history = [SYSTEM_PROMPT]

    chat_history.append({"role": "user", "content": msg})
    api_key = Config.PERPLEXITY_API_KEY

    if not api_key:
        return jsonify({"reply": "Missing API key"}), 500

    try:
        res = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"model": "sonar", "messages": chat_history}
        )

        print("📡 Status:", res.status_code)
        print("📨 Raw:", res.text)

        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"]
            chat_history.append({"role": "assistant", "content": content})

            # 💾 Сохраняем в БД
            db = SessionLocal()
            plan = TripAIPlan(input_message=msg, ai_reply=content)
            db.add(plan)
            db.commit()
            db.refresh(plan)
            db.close()

            try:
                structured = json.loads(content)
                return jsonify(success=True, plan=structured)
            except json.JSONDecodeError:
                return jsonify(reply=content)

        else:
            return jsonify(reply="Perplexity API error"), 500

    except Exception as e:
        print("❌ Chat error:", e)
        return jsonify(reply="Server error"), 500

@chat_bp.route("/chat/reset", methods=["POST"])
def reset_chat():
    global chat_history
    chat_history = [SYSTEM_PROMPT]
    return jsonify(success=True)
