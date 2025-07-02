from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from api.trips import trips_bp
from api.votes import votes_bp
from api.voting_rules import voting_bp
from api.auth import auth_bp
from api.chat import chat_bp
from flask_dance.contrib.github import make_github_blueprint, github
from routes.user import user_bp
import os
from dotenv import load_dotenv
from routes.session import session_bp
from routes.password_reset import reset_bp
from routes.notifications import notifications_bp
from utils.protect_blueprint import protect_blueprint
from routes.stripe_routes import stripe_bp

load_dotenv()


app = Flask(__name__)
CORS(app, supports_credentials=True)
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
app.register_blueprint(votes_bp)
app.register_blueprint(voting_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)

app.register_blueprint(user_bp)
app.register_blueprint(notifications_bp)

app.register_blueprint(stripe_bp)

print("📍 Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == "__main__":
    app.run(port=5001, debug=True)
