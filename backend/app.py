from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from api.trips import trips_bp
from api.votes import votes_bp
from api.voting_rules import voting_bp
from api.evaluate import evaluate_bp
from api.auth import auth_bp
from api.chat import chat_bp
from api.account import account_bp
from flask_dance.contrib.github import make_github_blueprint, github
import os
from dotenv import load_dotenv

load_dotenv()



app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(Config)
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
jwt = JWTManager(app)


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_OAUTH_CLIENT_SECRET"),
    scope="read:user,user:email",
    redirect_url="http://localhost:5001/api/github/callback"  
)



app.register_blueprint(github_bp)

app.register_blueprint(trips_bp)
app.register_blueprint(votes_bp)
app.register_blueprint(voting_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(account_bp)

print("📍 Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == "__main__":
    app.run(port=5001, debug=True)
