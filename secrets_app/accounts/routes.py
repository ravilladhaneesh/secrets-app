import random
from datetime import datetime, timedelta
import secrets
from flask import render_template, url_for, request, redirect, flash, Blueprint, session, abort
from secrets_app.forms import UserLoginForm, UserRegistrationForm, UserUpdateForm, AddSecretsForm, EmailVerificationForm
from secrets_app import app, db, bcrypt, login_manager, mail
from secrets_app.model import User, Secret, Nominee
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from urllib.parse import urlencode
import requests

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = UserRegistrationForm()
    if request.method == "POST":
        print(form.validate_on_submit() == True)
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if not user:
                otp = str(random.randint(100000, 999999))
                expiration_time = datetime.now() + timedelta(minutes=5)
                print(expiration_time)
                hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                user = User(
                    firstName=form.firstName.data,
                    lastName=form.lastName.data,
                    email=form.email.data,
                    password=hashed_pw,
                    otp=otp,
                    otp_expiration=expiration_time,
                    is_oauth=False,
                    is_verified=False)
                
                msg = Message("Your OTP Code", sender="ravilladhaneesh@gmail.com", recipients=[form.email.data])
                msg.body = f"Your OTP code is: {otp}"
                # mail.send(msg)

                db.session.add(user)
                db.session.commit()
                flash(f'Account created for email {form.email.data}!.You can now login in.', 'success')
                flash(f'OTP sent to email.Please verify your email', 'success')
                return redirect(url_for('accounts.login'))
            else:
                flash("Email Already registered.Please enter valid email")
        else:
            flash(f'Error Validating the form', 'danger')
    return render_template("register.html", form=form, title='register')




@accounts_bp.route("/verify", methods=["GET", "POST"])
@login_required
def verify():
    if not current_user.is_authenticated:
        return redirect(url_for("accounts.login"))
    userId = int(current_user.get_id())
    user = User.query.get(userId)
    if user.is_oauth or user.is_verified:
        flash("You are already verfied", "success")
        return redirect(url_for("home"))
    form = EmailVerificationForm()
    if request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            otp = form.otp.data

            if user and user.email == email:
                if user.otp == otp and user.otp_attempts < 3:
                    user.is_verified = True
                    user.otp_attempts = 0
                    user.otp = None
                    db.session.commit()
                    flash("Email Verified.", "success")
                    return redirect(url_for("home"))
                elif user.otp != otp and user.otp_attempts < 3:
                    print(user.otp_attempts)
                    user.otp_attempts += 1
                    db.session.commit()
                    flash("Invalid OTP.Enter Valid OTP", "danger")
                    
                elif user.otp_attempts >=3:
                    flash("Maximum Attempts Exceeded.Request new OTP", "danger")

                return redirect(url_for("accounts.verify"))
            else:
                flash("User not found", "danger")
        else:
            flash("Form Validation Failed", "danger")
        return redirect(url_for("accounts.verify"))
    form.email.data = user.email
    return render_template("verify.html", form=form, title="verify email")


@accounts_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    message = 'Login failed. Please check username and password'
    form = UserLoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and not user.is_oauth and bcrypt.check_password_hash(user.password, form.password.data):
                user.last_login = datetime.now()
                db.session.commit()
                login_user(user, remember=False)
                next = request.args.get("next")
                flash(f'Logged In as {user.firstName}', 'success')
                return redirect(next) if next else redirect(url_for('home'))
            elif user and user.is_oauth:
                message = "Please choose a valid login method"
        flash(message, 'danger')
    return render_template("login.html", form=form, title='login')




@accounts_bp.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('accounts.login'))




@accounts_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UserUpdateForm()
    userId = int(current_user.get_id())
    user = User.query.get(userId)
    if request.method == "POST":
        
        for field, errorMessage in form.errors.items():
            print(field, errorMessage)
        if user and form.validate_on_submit():
            user.firstName = form.firstName.data
            user.lastName = form.lastName.data
            user.required_login_per_days = form.required_login_per_days.data
            print(user.firstName, user.lastName, user.required_login_per_days)
            db.session.commit()
            flash("User Details Updated", 'success')
            return redirect(url_for('accounts.account'))
        print(form.errors)
        print("Hi")
    elif request.method == "GET":
        form.firstName.data = current_user.firstName
        form.lastName.data = current_user.lastName
        form.required_login_per_days.data = current_user.required_login_per_days
    return render_template('account.html', form=form)



@app.route('/authorize/<provider>')
def oauth2_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('home'))

    provider_data = app.config['OAUTH2_PROVIDERS'].get(provider)
    if provider_data is None:
        abort(404)

    # generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    # create a query string with all the OAuth2 parameters
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': url_for('oauth2_callback', provider=provider,
                                _external=True),
        'response_type': 'code',
        'scope': ' '.join(provider_data['scopes']),
        'state': session['oauth2_state'],
    })

    # redirect the user to the OAuth2 provider authorization URL
    return redirect(provider_data['authorize_url'] + '?' + qs)



@app.route('/callback/<provider>')
def oauth2_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('home'))

    provider_data = app.config['OAUTH2_PROVIDERS'].get(provider)
    if provider_data is None:
        abort(404)

    # if there was an authentication error, flash the error messages and exit
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('home'))
    # make sure that the state parameter matches the one we created in the
    # authorization request
    if request.args['state'] != session.get('oauth2_state'):
        abort(401)

    # make sure that the authorization code is present
    if 'code' not in request.args:
        abort(401)
    # exchange the authorization code for an access token
    response = requests.post(provider_data['token_url'], data={
        'client_id': provider_data['client_id'],
        'client_secret': provider_data['client_secret'],
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('oauth2_callback', provider=provider,
                                _external=True),
    }, headers={'Accept': 'application/json'})
    if response.status_code != 200:
        abort(401)
    oauth2_token = response.json().get('access_token')

    if not oauth2_token:
        abort(401)

    # use the access token to get the user's email address
    response = requests.get(provider_data['userinfo']['url'], headers={
        'Authorization': 'Bearer ' + oauth2_token,
        'Accept': 'application/json',
    })
    if response.status_code != 200:
        abort(401)
    email = provider_data['userinfo']['email'](response.json())

    # find or create the user in the database
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(
            firstName=email.split('@')[0],
            email=email,
            is_oauth=True,
            is_verified=True,
        )
        db.session.add(user)
        flash(f"Account created for email: {email}", "success")

    # log the user in
    user.last_login = datetime.now()
    db.session.commit()
    login_user(user)
    flash(f"Logged In as {user.firstName}", "success")
    return redirect(url_for('home'))