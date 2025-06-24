from flask import Blueprint, request, jsonify
import os
import requests

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

chat_history = []

SYSTEM_PROMPT = {
  "role": "system",
  "content": """ ... (весь твой prompt) ... """
}

@chat_bp.route('/perplexity-chat', methods=['POST'])
def perplexity_chat():
    global chat_history
    if not request.json:
        return jsonify({'reply': 'Invalid JSON data.'}), 400
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'reply': 'No input received.'}), 400
    if not chat_history:
        chat_history = [SYSTEM_PROMPT]
    chat_history.append({"role": "user", "content": user_message})
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY is missing.")
        return jsonify({'reply': 'Missing API key.'}), 500
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "sonar",
            "messages": chat_history
        }
        res = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=body)
        if res.status_code == 200:
            reply = res.json()["choices"][0]["message"]["content"]
            chat_history.append({"role": "assistant", "content": reply})
            return jsonify({'reply': reply})
        else:
            return jsonify({'reply': 'Perplexity API error'}), 500
    except Exception as e:
        print("❌ Exception:", e)
        return jsonify({'reply': 'Server error'}), 500

@chat_bp.route("/hello")
def hello():
    return jsonify(message="Hello from Flask!")

@chat_bp.route('/chat/reset', methods=['POST'])
def reset_chat():
    global chat_history
    chat_history = [SYSTEM_PROMPT]
    print("🔁 Chat history reset from frontend")
    return jsonify(success=True)
