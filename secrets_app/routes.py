from flask import render_template, url_for, request, redirect, flash
from secrets_app.forms import UserLoginForm, UserRegistrationForm
from secrets_app import app, db, bcrypt, login_manager
from secrets_app.model import User
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
def home():
    return render_template("home.html", title='home')



@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
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
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = UserLoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=False)
                next = request.args.get("next")
                flash(f'Logged In as {user.firstName}', 'success')
                return redirect(next) if next else redirect(url_for('home'))
        flash('Login failed. Please check username and password', 'danger')
    return render_template("login.html", form=form, title='login')


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/nominees")
@login_required
def nominees():
    return render_template("nominee.html", title='nominee')


@app.route("/account")
@login_required
def account():
    return render_template('account.html')