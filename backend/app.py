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

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(Config)
jwt = JWTManager(app)

app.register_blueprint(trips_bp)
app.register_blueprint(votes_bp)
app.register_blueprint(voting_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)

if __name__ == "__main__":
    app.run(port=5001, debug=True)
