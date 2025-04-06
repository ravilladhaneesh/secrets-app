from secrets_app import db, login_manager, app
from flask_login import UserMixin
from sqlalchemy.orm import backref
from sqlalchemy import PrimaryKeyConstraint
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(20), nullable=False)
    lastName = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(60), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=True)
    is_oauth = db.Column(db.Boolean, nullable=False, default=False)
    key = db.Column(db.String(60), nullable=True)
    secrets = db.relationship('Secret', backref=backref('user', passive_deletes=True), lazy=True, cascade='all, delete')
    last_login = db.Column(db.Date, nullable=False, default=datetime.now)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    send_email_authorized = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiration = db.Column(db.Date, nullable=True)
    otp_attempts = db.Column(db.Integer, default=0)
    required_login_per_days = db.Column(db.Integer, nullable=False, default=30)
    secret_salt = db.Column(db.String(30), nullable=False)
    oauth_refresh_token = db.Column(db.String(100), nullable=True)

    def get_reset_token(self):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.firstName}', '{self.lastName}, '{self.email}')"


class Secret(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fieldName = db.Column(db.String(100), nullable=False)
    fieldSecret = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    nominees = db.relationship('Nominee', backref='secret', cascade='all, delete', lazy=True) #Update to remove backref

    def __repr__(self):
        return f"Secret('{self.id}' '{self.fieldName}' '{self.user_id}')"

    def to_dict(self):
        return {
            'id': self.id,
            'fieldName': self.fieldName,
            'fieldSecret': self.fieldSecret,
            'nominees': [{'name': nominee.name, 'email_id': nominee.email_id} for nominee in self.nominees]
        }

class Nominee(db.Model):
    id = db.Column(db.Integer)
    name = db.Column(db.String(100))
    email_id = db.Column(db.String(100), primary_key=True)
    secret_id = db.Column(db.Integer, db.ForeignKey('secret.id', ondelete='CASCADE'), primary_key=True)
    # secret = db.relationship('Secret', backref=backref('nominees', passive_deletes=True), cascade='all, delete', lazy=True) can't be possible

    def __repr__(self):
        return f"Email('{self.name}', '{self.email_id})"
