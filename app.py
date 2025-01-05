from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from forms import UserRegistrationForm, UserLoginForm


app = Flask(__name__)
app.config['SECRET_KEY'] = "aaaaa"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///site.db"
db = SQLAlchemy(app)


class User(db.Model):
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


@app.route("/")
def home():
    return render_template("home.html", title='home')

@app.route("/register", methods=["GET", "POST"])
def register():
    form = UserRegistrationForm()
    if request.method == "POST":
        print(form.validate_on_submit() == True)
        if form.validate_on_submit():
            firstName = form.firstName.data
            flash(f'Account created for user {firstName}!', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Error Validating', 'warning')
    return render_template("register.html", form=form, title='register')


@app.route("/login", methods=["GET", "POST"])
def login():
    form = UserLoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            print(email)
            flash(f'Logged In as {email}', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Please check username and password', 'danger')
    return render_template("login.html", form=form, title='login')


@app.route("/nominees")
def nominees():
    return render_template("nominee.html", title='nominee')



if __name__ == "__main__":
    app.run(debug=True)
