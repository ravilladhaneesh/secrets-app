from secrets_app import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(20), nullable=False)
    lastName = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(60), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)
    key = db.Column(db.String(60), nullable=True)
    secrets = db.relationship('Secret', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.firstName}, {self.lastName}, {self.email}')"


class Secret(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fieldName = db.Column(db.String(100), nullable=False)
    fieldSecret = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emails = db.relationship('Email', backref='sentTo', lazy=True)

    def __repr__(self):
        return f"Secret('{self.id}' '{self.user_id}')"


class Email(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    email_address = db.Column(db.String(100), unique=True, nullable=False)
    secret_id = db.Column(db.Integer, db.ForeignKey('secret.id'))
    

    def __repr__(self):
        return f"Email('{self.email_address}')"
