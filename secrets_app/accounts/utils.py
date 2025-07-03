from cryptography.fernet import Fernet
from  google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from secrets_app.model import User
import google_auth_oauthlib.flow
from flask import current_app


def get_client_secrets(provider):
    return current_app.config.get("OAUTH2_PROVIDERS")[provider]


def encrypt(key, content):
    if content:
        f = Fernet(key)
        return f.encrypt(bytes(content, encoding="utf-8"))
    return None


def decrypt(key, token):
    if token:
        f = Fernet(key)
        return str(f.decrypt(token), encoding="utf-8")
    return None


def get_credentials_for_user(UserId):
    user = User.query.get(UserId)
    client_config = get_client_secrets("google")
    flow = google_auth_oauthlib.flow.Flow.from_client_config(client_config, scopes=client_config["web"]["scopes"].values())
    refresh_token = decrypt(user.secret_salt, user.oauth_refresh_token)
    
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=flow.client_config["token_uri"],
        client_id=flow.client_config["client_id"],
        client_secret=flow.client_config["client_secret"]
    )
    request = GoogleRequest()
    credentials.refresh(request)

    print(credentials.to_json())
    return credentials

