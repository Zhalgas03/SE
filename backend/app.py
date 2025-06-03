# app.py

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config

# Импорт блюпринтов
from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from trip import trip_bp  # ✅ Новый импорт

def create_app():
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY

    # JWT и CORS
    jwt = JWTManager(app)
    CORS(app, supports_credentials=True)

    # Регистрация маршрутов
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(trip_bp)  # ✅ Подключен Trip API

    @app.route("/api/hello")
    def hello():
        return jsonify(message="Hello from Flask!")

    return app

if __name__ == "__main__":
    app = create_app()

    # ✅ Создание таблиц в PostgreSQL при запуске
    from db import Base, engine
    import models.ai_plan  # 👈 Регистрируем модель
    Base.metadata.create_all(bind=engine)

    app.run(port=5001, debug=True)
