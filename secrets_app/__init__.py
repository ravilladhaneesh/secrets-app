from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from secrets_app.config import Config


db = SQLAlchemy()

mail = Mail()

migrate = Migrate()

bcrypt = Bcrypt()

login_manager = LoginManager()
login_manager.login_view = 'accounts.login'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from secrets_app.accounts.routes import accounts_bp
    from secrets_app.secrets.routes import secrets_bp
    from secrets_app.main.routes import main_bp

    app.register_blueprint(accounts_bp)
    app.register_blueprint(secrets_bp)
    app.register_blueprint(main_bp)

    from secrets_app import schedule_email


    return app


