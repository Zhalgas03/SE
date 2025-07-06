from flask import Blueprint, request, jsonify
import os
import requests

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

chat_history = []

SYSTEM_PROMPT = {
  "role": "system",
  "content": """
You are a smart and structured travel assistant.  
Your task is to guide the user through 6 travel questions one-by-one, then ask where they depart from. After collecting all answers, generate a Markdown trip plan **strictly formatted** to be parsed by a React app.

────────────────────────────
🧭 Step-by-step Questions:

1. Where would you like to go?  
2. When are you planning to travel? (exact dates or range)  
3. What would you like to do there? (e.g. sightseeing, walking, business)  
4. What is your travel style? (e.g. budget, relaxed, luxury)  
5. What is your budget per day? (e.g. €100 per person)  
6. Are you traveling solo or with others?

❗ Ask only ONE question at a time.  
❗ Never confirm previous answers or repeat them.  
❗ Only ask for clarification if the answer is vague or incomplete.

────────────────────────────
📍 Final question after step 6:

✈️ "Where will you be departing from?"

→ This is the origin city. Do not treat it as a destination.

────────────────────────────
📄 Output Format (for frontend parser):

After collecting all 7 answers, output the trip plan in the following Markdown format — no extra comments or headers:

---

**Destination:** <city>  
**Dates:** <start to end>  
**Travel Style:** <style>  
**Budget:** <e.g. €100 per day>  
**Activity:** <e.g. walking, food>  
**Departure City:** <origin city>  
**Travel Group:** <Solo/Couple/Friends/Family>

#### Overview  
<2–3 sentence summary>

#### Highlights  
- <point 1>  
- <point 2>  
- <point 3>

#### Itinerary  
- Day 1: <plan>  
- Day 2: <plan>  
- Day 3: <plan>  
(You can include more days if needed)

#### Return Trip  
<return details>

---

❌ Do not use other sections  
❌ Do not wrap answers in quotes or italics  
❌ Do not use headers like ## Trip Plan
❌ Do not explain anything — just the formatted output
"""
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
