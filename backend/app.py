from flask import Flask
from flask_cors import CORS
<<<<<<< HEAD
from flask_jwt_extended import JWTManager
from config import Config
from api.trips import trips_bp
from api.votes import votes_bp
from api.voting_rules import voting_bp
from api.evaluate import evaluate_bp
from api.auth import auth_bp
from api.chat import chat_bp
from flask_dance.contrib.github import make_github_blueprint, github
from routes.user import user_bp
import os
from dotenv import load_dotenv
from routes.session import session_bp
from routes.password_reset import reset_bp
from routes.notifications import notifications_bp




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



app.register_blueprint(github_bp)

app.register_blueprint(session_bp)

app.register_blueprint(user_bp)

app.register_blueprint(reset_bp)

app.register_blueprint(notifications_bp)



app.register_blueprint(trips_bp)
app.register_blueprint(votes_bp)
app.register_blueprint(voting_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)


print("📍 Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == "__main__":
    app.run(port=5001, debug=True)
=======
from models import db
from models.trip import Trip, VotingRule, Vote  # Ensure models are imported
from routes.trip_routes import trip_routes
from routes.vote_routes import vote_routes
from routes.auth_routes import auth_routes
import os
from flask_jwt_extended import JWTManager

def create_app(test_config=None):
    app = Flask(__name__)
    if test_config:
        app.config.update(test_config)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Enable CORS for frontend
    CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

    db.init_app(app)
    # Set JWT secret key if not set
    if not app.config.get('JWT_SECRET_KEY'):
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key')
    # Initialize JWTManager
    JWTManager(app)
    app.register_blueprint(trip_routes)
    app.register_blueprint(vote_routes)
    app.register_blueprint(auth_routes)

    @app.route('/')
    def index():
        return 'OK'

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
>>>>>>> 276f72e77590322f9f8c422c79f4ba32443e7c4f
