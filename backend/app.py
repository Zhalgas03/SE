from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
import re  # <-- ДОБАВЬ СЮДА!
import pymysql

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'tripuser'
app.config['MYSQL_PASSWORD'] = 'trippass'
app.config['MYSQL_DB'] = 'tripdb'

# JWT config
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

mysql = MySQL(app)
jwt = JWTManager(app)

@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask!")



@app.route('/api/register', methods=['POST'])
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # Проверка на пустые поля
    if not all([username, email, password]):
        return jsonify(success=False, message="All fields are required."), 400

    # ✅ Проверка: username должен содержать хотя бы одну букву (латиница)
    if not re.search(r'[a-zA-Z]', username):
        return jsonify(success=False, message="Username must contain at least one letter."), 400

    # Email валидация
    try:
        validate_email(email)
    except EmailNotValidError:
        return jsonify(success=False, message="Invalid email address."), 400

    # Проверка пароля по стандарту
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
        return jsonify(success=False, message="Password must be at least 8 characters and include uppercase, lowercase letters and a number."), 400

    hashed_password = generate_password_hash(password)

    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password))
        mysql.connection.commit()
        cur.close()
        return jsonify(success=True, message="User registered successfully."), 201

    except Exception as e:
        error_msg = str(e)
        if "Duplicate entry" in error_msg and "username" in error_msg:
            return jsonify(success=False, message="This username is already taken. Please choose another."), 409
        elif "Duplicate entry" in error_msg and "email" in error_msg:
            return jsonify(success=False, message="This email is already registered. Please use another."), 409
        else:
            print("Unexpected error:", error_msg)
            return jsonify(success=False, message="Unexpected server error"), 500



@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password_input = data.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[3], password_input):
        access_token = create_access_token(identity={'username': user[1], 'email': user[2]})
        return jsonify(success=True, token=access_token, username=user[1]), 200
    else:
        return jsonify(success=False, message="Invalid email or password"), 401

    except Exception as e:
        print("Login error:", str(e))
        return jsonify(success=False, message="Server error"), 500


chat_history = []

SYSTEM_PROMPT = {
  "role": "system",
  "content": """
You are a structured and intelligent travel planner assistant.

Your job is to guide the user through 6 structured questions, one by one, in this exact order:

1. Where would you like to go?
2. When are you planning to travel?
3. What do you want to do there? (e.g. business, sightseeing, food, walking)
4. What is your travel style? (e.g. budget, relaxed, adventurous)
5. What is your budget?
6. Are you traveling solo or with others?

────────────────────────────
🧠 Answer handling rules:

– Ask only **one question per message**.  
– After receiving a valid and complete answer, immediately move to the **next unanswered** question.  
– Do **not** repeat, rephrase, confirm, or echo the user's response.  
– Only ask for clarification if:
  • the answer is vague or incomplete (e.g. "somewhere", "soon", "5 days")  
  • the user contradicts an earlier answer  
  • the answer cannot be used without further detail  
– If the answer is clear, move on confidently.

────────────────────────────
📅 Date handling (Question 2):

Your goal is to obtain a **full travel date range** (start + end). Handle answers as follows:

– If user gives a full range ("from 10 July to 15 July"), accept and convert both to ISO date format.  
– If user gives relative date + duration ("next Monday for 5 days"), calculate both absolute dates based on current day (assume Europe/Rome timezone).  
– If user gives only a start date, ask:
  "Please specify how many days you'll stay, or provide an end date."  
– If user gives only duration (e.g. "5 days"), ask:
  "Please tell me when your trip starts so I can calculate the full range."  
– Always store both start and end dates before moving on.

────────────────────────────
🌍 Location clarification (Question 1):

– If user gives only a country, vague area, or general direction (e.g. "Germany", "somewhere warm", "north"), ask them to name a **specific city**.  
– Offer 2–3 city name suggestions **without description**, e.g.:
  "Can you specify a city? Suggestions: Berlin, Munich, Hamburg."

────────────────────────────
🧳 After Question 6 (Travel group):

Ask one final question before generating a plan:

✈️ "Where will you be departing from?"

– Treat this as the **origin city** for transportation planning.  
– Do **not** treat this as a new destination.  
– Do **not** restart the question flow.  
– Do **not** ask "Where would you like to go?" again.  
– After receiving the departure city, immediately generate the **trip summary** and a **full travel plan** (transport, hotels, POIs, suggestions).

────────────────────────────
✍️ Summary & Travel Plan:

After collecting all 7 items (destination, date range, activity, style, budget, group, origin), do the following:

1. Present a bullet point summary of the trip inputs.  
2. Generate a detailed travel plan including:
   – recommended hotels (within budget)  
   – suggested activities and POIs  
   – practical travel tips  
   – transportation options (from origin to destination and return)

Keep responses structured, minimal, and clear.
"""
}



@app.route('/api/perplexity-chat', methods=['POST'])
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

        print("Perplexity status code:", res.status_code)
        print("Perplexity response:", res.text)

        if res.status_code == 200:
            reply = res.json()["choices"][0]["message"]["content"]
            chat_history.append({"role": "assistant", "content": reply})
            return jsonify({'reply': reply})
        else:
            return jsonify({'reply': 'Perplexity API error'}), 500

    except Exception as e:
        print("❌ Exception:", e)
        return jsonify({'reply': 'Server error'}), 500


@app.route("/api/hello")
def hello():
    return jsonify(message="Hello from Flask!")

@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    global chat_history
    chat_history = [SYSTEM_PROMPT]
    print("🔁 Chat history reset from frontend")
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
