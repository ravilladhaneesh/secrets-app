import random
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from flask import current_app, render_template, url_for, request, redirect, flash, Blueprint, session, abort
from secrets_app.accounts.forms import (UserLoginForm, UserRegistrationForm, UserUpdateForm
                               , EmailVerificationForm, ResetPasswordForm, RequestResetForm)
from secrets_app.secrets.forms import AddSecretsForm
from secrets_app import db, bcrypt
from secrets_app.model import User
from flask_login import login_user, current_user, logout_user, login_required
import requests
from  google.oauth2.credentials import Credentials
import google_auth_oauthlib.flow
import google.auth.transport.requests
from secrets_app.accounts.google_oauth_creds import get_credentials
from secrets_app.accounts.mail_service import gmail_send_message, send_otp_from_root_account, send_reset_email
from secrets_app.accounts.utils import get_client_secrets, encrypt, decrypt, get_credentials_for_user

accounts_bp = Blueprint("accounts", __name__)

SCOPES = {
    "userinfo": 'https://www.googleapis.com/auth/userinfo.email',
    "sendmessage": 'https://www.googleapis.com/auth/gmail.send',
    "userinfo_profile": 'https://www.googleapis.com/auth/userinfo.profile'
}

def credentials_to_dict(credentials):
  return {'access_token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes,
          'granted_scopes': credentials.granted_scopes}


@accounts_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
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
                salt = Fernet.generate_key().decode('utf-8')
                print(salt)
                user = User(
                    firstName=form.firstName.data,
                    lastName=form.lastName.data,
                    email=form.email.data,
                    password=hashed_pw,
                    secret_salt=salt,
                    otp=otp,
                    otp_expiration=expiration_time,
                    is_oauth=False,
                    is_verified=False,
                    send_email_authorized=False)
                
                send_otp_from_root_account(otp, form.email.data)

                db.session.add(user)
                db.session.commit()
                flash(f'Account created for email {form.email.data}!.You can now login in.', 'success')
                flash(f'OTP sent to email.Please verify your email', 'success')
                return redirect(url_for('accounts.verify'))
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
        next = request.args.get('next')
        flash("You are already verfied", "success")
        return redirect(next) if next else redirect(url_for("main.home"))
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
                    return redirect(url_for("main.home"))
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
        return redirect(url_for('main.home'))
    message = 'Login failed. Please check username and password'
    form = UserLoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.password and bcrypt.check_password_hash(user.password, form.password.data):
                user.last_login = datetime.now()
                db.session.commit()
                login_user(user, remember=False)
                next = request.args.get("next")
                flash(f'Logged In as {user.firstName}', 'success')
                verification_alert_shown = True
                if not user.is_oauth and not user.is_verified:
                    verification_alert_shown = False
                return redirect(next) if next else redirect(url_for('main.home', verification_alert_shown=verification_alert_shown))
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



@accounts_bp.route('/authorize/<provider>')
def oauth2_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('main.home'))

    client_config = get_client_secrets(provider)
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
      client_config=client_config, scopes=SCOPES["userinfo"])

    flow.redirect_uri = url_for('accounts.oauth2_callback', provider=provider, _external=True)
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    # qs = build_query_encoder(provider_data, redirect_uri, scope)

    # redirect the user to the OAuth2 provider authorization URL
    return redirect(authorization_url)



@accounts_bp.route('/callback/<provider>')
def oauth2_callback(provider):
    print("HELLO")
    if not current_user.is_anonymous:
        return redirect(url_for('main.home'))

    client_config = get_client_secrets(provider)
    for i in session:
        print(i, session[i])
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=client_config, scopes=SCOPES["userinfo"], state=state)
    flow.redirect_uri = url_for('accounts.oauth2_callback', provider=provider, _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    print(authorization_response, "authorization_response")
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    credentials = credentials_to_dict(credentials)

    if 'access_token' not in credentials:
        abort(401)
    
    
    response = requests.get(client_config['web']['userinfo']['url'], headers={
        'Authorization': 'Bearer ' + credentials["access_token"],
        'Accept': 'application/json',
    })

    if response.status_code != 200:
        abort(401)
    email = client_config['web']['userinfo']['email'](response.json())
    print(credentials)
    # find or create the user in the database
    user = User.query.filter_by(email=email).first()
    if user is None:
        if credentials["refresh_token"]:
            salt = Fernet.generate_key().decode('utf-8')
            token = encrypt(salt, credentials["refresh_token"])
            user = User(
                firstName=email.split('@')[0],
                email=email,
                is_oauth=True,
                is_verified=True,
                send_email_authorized=False,
                secret_salt=salt,
                oauth_refresh_token=token
            )
            db.session.add(user)
            flash(f"Account created for email: {email}", "success")
        else:
            flash("Unable to create new account for user.Please check and delete the application from google's third party application and retry.", "danger")
            return redirect(url_for("main.home"))
    else:
        if not user.is_oauth:
            user.is_oauth = True
            if credentials["refresh_token"]:
                token = encrypt(user.secret_salt, credentials["refresh_token"])
                user.oauth_refresh_token = token

    # log the user in
    user.last_login = datetime.now()
    db.session.commit()
    login_user(user)
    flash(f"Logged In as {user.firstName}", "success")
    return redirect(url_for('main.home'))



@accounts_bp.route("/authorize/sendmessage/<provider>")
@login_required
def authorize_send_message(provider):
    if current_user.is_anonymous:
        return redirect(url_for("accounts.login"))

    client_config = get_client_secrets(provider)
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
      client_config=client_config, scopes=[SCOPES["userinfo"], SCOPES["sendmessage"]])
    flow.redirect_uri = url_for('accounts.verify_send_message', provider=provider, _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    session['state'] = state
    return redirect(authorization_url)


@accounts_bp.route("/callback/verifySentMessage/<provider>")
@login_required
def verify_send_message(provider):
    if current_user.is_anonymous:
        return redirect(url_for("accounts.login"))
    

    client_config = get_client_secrets(provider)
    if client_config is None:
        abort(404)

    # if there was an authentication error, flash the error messages and exit
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('main.home'))
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=client_config, scopes=SCOPES["sendmessage"], state=state)
    flow.redirect_uri = url_for('accounts.verify_send_message', provider=provider, _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    credentials = credentials_to_dict(credentials)
    print(credentials)

    if SCOPES["sendmessage"] in credentials["granted_scopes"]:
        response = requests.get(client_config['web']['userinfo']['url'], headers={
        'Authorization': 'Bearer ' + credentials["access_token"],
        'Accept': 'application/json',
        })

        if response.status_code != 200:
            abort(401)
        email = client_config['web']['userinfo']['email'](response.json())
        userId = int(current_user.get_id())
        user = User.query.get(userId)
        print(user.email, email)
        token = encrypt(user.secret_salt, credentials["refresh_token"])
        if user.email == email:
            if credentials["refresh_token"]:
                user.send_email_authorized = True
                user.oauth_refresh_token = token
                
                db.session.commit()
                flash("Send mail verified", "success")
            else:
                flash("Unable to create new account for user.Please check and delete the application from google's third party application and retry.", "danger")
        else:
            flash("Please authenticate with the registered email ID", "danger")
    return redirect(url_for("main.home"))


@accounts_bp.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('accounts.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)



@accounts_bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('accounts.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('accounts.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)



def send_otp(recipients):
    pass


@accounts_bp.route("/test2")
def test2():
    SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    # Add other requested scopes.
    ]
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
      client_config=get_client_secrets("google"), scopes=SCOPES)
    
    flow.redirect_uri = url_for('accounts.callback2', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    session['state'] = state

    return redirect(authorization_url)

@accounts_bp.route("/callback2")
def callback2():
    state = session["state"]
    SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    # Add other requested scopes.
    ]
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=get_client_secrets("google"), scopes=SCOPES, state=state)
    authorization_response = request.url
    flow.redirect_uri = "http://localhost:5000/callback2"
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    print(credentials.to_json())
    #get_credentials(request, state)
    return redirect(url_for("main.home"))


@accounts_bp.route("/scopes")
@login_required
def scopes():
    credentials = get_credentials_for_user(int(current_user.get_id()))
    url = "https://www.googleapis.com/oauth2/v1/tokeninfo"
    response = requests.get(url, params={"access_token": credentials.token})
    print(response.json())
    flash(response.json(), "success")
    return redirect(url_for("main.home"))


@accounts_bp.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    print("Delete Account")
    print(request)
    if not current_user.is_authenticated:
        return redirect(url_for('accounts.login'))
    print(request)
    if request.method == "POST":
        user = User.query.get(int(current_user.id))
        if user:
            db.session.delete(user)
            db.session.commit()
            flash("Your account has been deleted.", "success")
        else:
            flash("User not found.", "danger")
        return redirect(url_for("main.home"))
    return render_template("account.html", title="Delete Account")