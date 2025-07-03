import os
from dotenv import load_dotenv
load_dotenv()



class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")
    
    
    ROOT_EMAIL = os.environ.get("ROOT_EMAIL")

    GOOGLE_LOGIN_REDIRECT_SCHEME = 'https'
    print(os.getenv("GOOGLE_CLIENT_SECRETS"),"-->\n\n\n")
    OAUTH2_PROVIDERS = {
            # Google OAuth 2.0 documentation:
            # https://developers.google.com/identity/protocols/oauth2/web-server#httprest
            'google': {
                    'web': {
                        'client_id': os.getenv("GOOGLE_CLIENT_ID"),
                        'client_secret': os.getenv("GOOGLE_CLIENT_SECRETS") ,
                        "project_id": "secure-secrets",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        'userinfo': {
                            'url': 'https://www.googleapis.com/oauth2/v3/userinfo',
                            'email': lambda json: json['email'],
                        },
                        'scopes': {
                                    "userinfo": 'https://www.googleapis.com/auth/userinfo.email',
                                    "sendmessage": 'https://www.googleapis.com/auth/gmail.send'
                                }
                    }
                }
            }
