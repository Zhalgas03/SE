from flask import Blueprint, request, jsonify
from services.system_prompt import SYSTEM_PROMPT
from config import Config
import requests

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
        res = requests.post("https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"model": "sonar", "messages": chat_history}
        )

        if res.status_code == 200:
            reply = res.json()["choices"][0]["message"]["content"]
            chat_history.append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "Perplexity API error"}), 500

    except Exception as e:
        print("❌ Chat error:", e)
        return jsonify({"reply": "Server error"}), 500

@chat_bp.route("/chat/reset", methods=["POST"])
def reset_chat():
    global chat_history
    chat_history = [SYSTEM_PROMPT]
    return jsonify(success=True)
