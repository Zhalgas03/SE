# services/oauth_service.py
from flask import session
from requests_oauthlib import OAuth2Session
from config import Config

AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

def get_google_auth(state=None, token=None):
    return OAuth2Session(
        Config.GOOGLE_CLIENT_ID,
        redirect_uri=Config.REDIRECT_URI,
        scope=["openid", "email", "profile"],
        state=state,
        token=token
    )

def get_user_info(token, request_url):
    google = get_google_auth(state=session["oauth_state"])
    google.fetch_token(TOKEN_URL, client_secret=Config.GOOGLE_CLIENT_SECRET, authorization_response=request_url)
    return google.get(USER_INFO_URL).json()
