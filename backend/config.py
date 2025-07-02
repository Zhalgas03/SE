from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    # RECAPTCHA_SECRET_KEY = os.getenv("6Lc39msrAAAAADyNY5DlKzRtAObnZh-hJrLmlSzC")
    RECAPTCHA_SECRET_KEY = ("6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")