from flask import render_template, url_for, request, redirect, flash
from secrets_app.forms import UserLoginForm, UserRegistrationForm
from secrets_app import app, db, bcrypt
from secrets_app.model import User

@app.route("/")
def home():
    return render_template("home.html", title='home')

@app.route("/register", methods=["GET", "POST"])
def register():
    form = UserRegistrationForm()
    if request.method == "POST":
        print(form.validate_on_submit() == True)
        if form.validate_on_submit():
            hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(firstName=form.firstName.data, lastName=form.lastName.data, email=form.email.data, password=hashed_pw)
            db.session.add(user)
            db.session.commit()
            flash(f'Account created for email {form.email.data}!.You can now login in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Error Validating the form', 'danger')
    return render_template("register.html", form=form, title='register')


@app.route("/login", methods=["GET", "POST"])
def login():
    form = UserLoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                flash(f'Logged In as {user.firstName}', 'success')
                return redirect(url_for('home'))
        flash('Login failed. Please check username and password', 'danger')
    return render_template("login.html", form=form, title='login')


@app.route("/nominees")
def nominees():
    return render_template("nominee.html", title='nominee')
