from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from api.trips import trips_bp
from api.votes import votes_bp
from api.voting_rules import voting_bp
from api.auth import auth_bp
from api.chat import chat_bp
from flask_dance.contrib.github import make_github_blueprint, github
from routes.user import user_bp
from dotenv import load_dotenv
from routes.session import session_bp
from routes.password_reset import reset_bp
from routes.notifications import notifications_bp
from utils.protect_blueprint import protect_blueprint
from routes.stripe_routes import stripe_bp
from services.system_prompt import SYSTEM_PROMPT
from flask import send_from_directory

load_dotenv()


app = Flask(__name__)

# Enhanced CORS configuration
CORS(app, 
     origins=["http://localhost:3000", "http://localhost:3001"], 
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"],
     expose_headers=["Content-Type", "Authorization"],
     max_age=3600)

app.config.from_object(Config)
jwt = JWTManager(app)


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_OAUTH_CLIENT_SECRET"),
    scope="read:user,user:email"
)


protect_blueprint(user_bp, require_login=True)

protect_blueprint(notifications_bp, require_login=True, require_subscription=True)

app.register_blueprint(github_bp)

app.register_blueprint(session_bp)


app.register_blueprint(reset_bp)




app.register_blueprint(trips_bp)
print("✅ Registered trips_bp blueprint")
app.register_blueprint(votes_bp)
print("✅ Registered votes_bp blueprint")
app.register_blueprint(voting_bp)
print("✅ Registered voting_bp blueprint")
app.register_blueprint(auth_bp)
print("✅ Registered auth_bp blueprint")
app.register_blueprint(chat_bp)
print("✅ Registered chat_bp blueprint")

app.register_blueprint(user_bp)
app.register_blueprint(notifications_bp)

app.register_blueprint(stripe_bp)




print("📍 Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule)

@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    global chat_history
    chat_history = [SYSTEM_PROMPT]
    print("🔁 Chat history reset from frontend")
    return jsonify(success=True)

@app.route('/static/trips/<filename>')
def serve_pdf(filename):
    return send_from_directory("static/trips", filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    print(f"🎯 STATIC FILE: Serving {filename}")
    try:
        return send_from_directory('../frontend/build/static', filename)
    except FileNotFoundError:
        print(f"❌ Static file not found: {filename}")
        return jsonify({"error": "Static file not found"}), 404

# Catch-all route to serve React app for client-side routing
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    print(f"🎯 CATCH-ALL ROUTE: Serving React app for path: {path}")
    
    # Don't serve React app for API routes
    if path.startswith('api/'):
        print(f"❌ API route requested: {path}")
        return jsonify({"error": "API route not found"}), 404
    
    # Don't serve React app for static files
    if path.startswith('static/'):
        print(f"❌ Static file requested: {path}")
        return jsonify({"error": "Static file not found"}), 404
    
    # Serve index.html for all other routes (client-side routing)
    try:
        index_path = os.path.join(os.path.dirname(__file__), '../frontend/build/index.html')
        print(f"✅ Serving index.html from: {index_path}")
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                content = f.read()
            print(f"✅ index.html content length: {len(content)} characters")
            return content, 200, {'Content-Type': 'text/html'}
        else:
            print(f"❌ index.html not found at: {index_path}")
            return jsonify({"error": "React app not built"}), 404
    except Exception as e:
        print(f"❌ Error serving index.html: {e}")
        return jsonify({"error": "React app not built"}), 404

if __name__ == "__main__":
    app.run(port=5001, debug=True)