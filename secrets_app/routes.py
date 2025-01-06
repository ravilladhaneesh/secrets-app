from flask import render_template, url_for, request, redirect, flash
from secrets_app.forms import UserLoginForm, UserRegistrationForm
from secrets_app import app

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
