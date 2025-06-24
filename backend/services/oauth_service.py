from requests_oauthlib import OAuth2Session
from flask import session
from config import Config

def get_google_auth(state=None, token=None):
    return OAuth2Session(
        Config.GOOGLE_CLIENT_ID,
        redirect_uri=Config.REDIRECT_URI,
        scope=["openid", "email", "profile"],
        state=state,
        token=token
    )

def get_user_info(request_url):
    google = get_google_auth(state=session.get("oauth_state"))
    token = google.fetch_token(
        Config.TOKEN_URL,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        authorization_response=request_url
    )
    return google.get(Config.USER_INFO_URL).json()
