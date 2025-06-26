from flask import Flask
from flask_cors import CORS
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
