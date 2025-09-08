from flask import Flask, jsonify
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
import click



load_dotenv()

from routes.session import session_bp
from routes.password_reset import reset_bp
from routes.notifications import notifications_bp
from utils.protect_blueprint import protect_blueprint
from routes.stripe_routes import stripe_bp
from services.system_prompt import SYSTEM_PROMPT
from flask import send_from_directory
from routes.admin import admin_bp
from api.transport import transport_bp
from api.hotel import hotel_bp
from routes.weekly_routes import weekly_bp
from routes.weekly_optin import weekly_optin_bp

from api.weekly_generate import weekly_api_bp

from api.weekly_job import run_weekly_dry_run, run_weekly_dispatch



app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(Config)
jwt = JWTManager(app)

# ---- Email config (единый источник правды) ----
email_sender = os.getenv("EMAIL_SENDER", "vperedmuslims@gmail.com")  # чистый адрес (логин)
email_from = os.getenv("EMAIL_FROM", f"Trip DVisor <{email_sender}>") # display From
app.config["EMAIL_FROM"] = email_from
app.config["EMAIL_SENDER"] = email_sender
app.config.setdefault("JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "dev-jwt"))
# -----------------------------------------------



os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_OAUTH_CLIENT_SECRET"),
    scope="read:user,user:email"
)


protect_blueprint(user_bp, require_login=True)

protect_blueprint(notifications_bp, require_login=True, require_subscription=True)
app.register_blueprint(admin_bp)
app.register_blueprint(github_bp)

app.register_blueprint(session_bp)
app.register_blueprint(hotel_bp)

app.register_blueprint(reset_bp)

app.register_blueprint(weekly_bp)


app.register_blueprint(trips_bp)
app.register_blueprint(votes_bp)
app.register_blueprint(voting_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)

app.register_blueprint(user_bp)
app.register_blueprint(notifications_bp)

app.register_blueprint(stripe_bp)

app.register_blueprint(transport_bp)


import click
from api.weekly_job import run_weekly_dry_run, run_weekly_dispatch

app.register_blueprint(weekly_optin_bp)

app.register_blueprint(weekly_api_bp)

@app.cli.command("weekly-dry-run")
@click.option("--mode", default="llm", type=click.Choice(["auto","llm","basic"]), show_default=True)
@click.option("--salt", default=None, help="Variability seed within the week")
@click.option("--destination", default=None, help="Override destination (e.g., 'Rome, Italy')")
@click.option("--duration", default=None, help="3..5 days")
def weekly_dry_run_cmd(mode, salt, destination, duration):
    out = run_weekly_dry_run(app, mode=mode, salt=salt, destination=destination, duration=duration)
    click.echo(out)

@app.cli.command("weekly-send-one")
@click.option("--email", required=True, help="Send Weekly to a single address.")
@click.option("--mode", default="llm", type=click.Choice(["auto","llm","basic"]), show_default=True)
@click.option("--salt", default=None, help="Variability seed within the week")
@click.option("--destination", default=None)
@click.option("--duration", default=None)
def weekly_send_one_cmd(email, mode, salt, destination, duration):
    out = run_weekly_dispatch(app, only_email=email, mode=mode, salt=salt, destination=destination, duration=duration)
    click.echo(out)

@app.cli.command("weekly-run")
@click.option("--mode", default="llm", type=click.Choice(["auto","llm","basic"]), show_default=True)
@click.option("--salt", default=None, help="Variability seed within the week")
@click.option("--destination", default=None)
@click.option("--duration", default=None)
def weekly_run_cmd(mode, salt, destination, duration):
    out = run_weekly_dispatch(app, mode=mode, salt=salt, destination=destination, duration=duration)
    click.echo(out)

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

if __name__ == "__main__":
    app.run(port=5001, debug=True)