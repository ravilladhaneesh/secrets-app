import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = "f0af40cd6604cf9f13a166212c656a833f80729e521145627af719a3700d46e2"

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///site.db"
db = SQLAlchemy(app)




# Email configuration

mail = Mail(app)

app.config['OAUTH2_PROVIDERS'] = {
    # Google OAuth 2.0 documentation:
    # https://developers.google.com/identity/protocols/oauth2/web-server#httprest
            'google': {
            'client_id': os.getenv("GOOGLE_CLIENT_ID"),
            'client_secret': os.getenv("GOOGLE_CLIENT_SECRETS") ,
            'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
            'token_url': 'https://accounts.google.com/o/oauth2/token',
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



migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'accounts.login'

from secrets_app.accounts.routes import accounts_bp
from secrets_app import routes

app.register_blueprint(accounts_bp)