import random
from datetime import datetime, timedelta
import secrets
from cryptography.fernet import Fernet
from flask import render_template, url_for, request, redirect, flash, Blueprint, session, abort
from secrets_app.forms import UserLoginForm, UserRegistrationForm, UserUpdateForm, AddSecretsForm, EmailVerificationForm
from secrets_app import app, db, bcrypt, login_manager, mail
from secrets_app.model import User, Secret, Nominee
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from urllib.parse import urlencode
import requests
from  google.oauth2.credentials import Credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import google.auth.transport.requests
from secrets_app.accounts.google_oauth_creds import get_credentials
from secrets_app.accounts.mail_service import gmail_send_message, send_otp_from_root_account


accounts_bp = Blueprint("accounts", __name__)

CLIENT_SECRETS_FILE = "client_secret.json"

SCOPES = {"userInfo": 'https://www.googleapis.com/auth/userinfo.email',
          "sendMail": 'https://www.googleapis.com/auth/gmail.send'}


# def build_query_encoder(provider_data, redirect_uri, scope):
#     if provider_data is None:
#         abort(404)

#     # generate a random string for the state parameter
#     session['oauth2_state'] = secrets.token_urlsafe(16)

#     # create a query string with all the OAuth2 parameters
#     qs = urlencode({
#         'client_id': provider_data['client_id'],
#         'redirect_uri': redirect_uri,
#         'response_type': 'code',
#         'scope': scope,
#         'state': session['oauth2_state'],
#     })

#     return qs



def credentials_to_dict(credentials):
  return {'access_token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'granted_scopes': credentials.granted_scopes}


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
                
                # send_otp_from_root_account(otp, form.email.data)

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



@accounts_bp.route('/authorize/<provider>')
def oauth2_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('home'))

    # provider_data = app.config['OAUTH2_PROVIDERS'].get(provider)
    # redirect_uri = url_for('accounts.oauth2_callback', provider=provider, _external=True)
    # scope = 

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES["userInfo"])
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
    # return redirect(provider_data['authorize_url'] + '?' + qs)
    return redirect(authorization_url)



@accounts_bp.route('/callback/<provider>')
def oauth2_callback(provider):
    print("HELLO")
    if not current_user.is_anonymous:
        return redirect(url_for('home'))

    provider_data = app.config['OAUTH2_PROVIDERS'].get(provider)
    # if provider_data is None:
    #     abort(404)

    # # if there was an authentication error, flash the error messages and exit
    # if 'error' in request.args:
    #     for k, v in request.args.items():
    #         if k.startswith('error'):
    #             flash(f'{k}: {v}')
    #     return redirect(url_for('home'))
    # # make sure that the state parameter matches the one we created in the
    # # authorization request
    # if request.args['state'] != session.get('oauth2_state'):
    #     abort(401)

    # # make sure that the authorization code is present
    # if 'code' not in request.args:
    #     abort(401)
    # # exchange the authorization code for an access token
    # response = requests.post(provider_data['token_url'], data={
    #     'client_id': provider_data['client_id'],
    #     'client_secret': provider_data['client_secret'],
    #     'code': request.args['code'],
    #     'grant_type': 'authorization_code',
    #     'access_type': 'offline',
    #     'prompt': 'consent',
    #     'redirect_uri': url_for('accounts.oauth2_callback', provider=provider,
    #                             _external=True),
    # }, headers={'Accept': 'application/json'})

    # if response.status_code != 200:
    #     abort(401)
    # print(response.json())
    # oauth2_token = response.json().get('access_token')

    # if not oauth2_token:
    #     abort(401)

    # # use the access token to get the user's email address
    # response = requests.get(provider_data['userinfo']['url'], headers={
    #     'Authorization': 'Bearer ' + oauth2_token,
    #     'Accept': 'application/json',
    # })
    # if response.status_code != 200:
    #     abort(401)
    # email = provider_data['userinfo']['email'](response.json())

    # # find or create the user in the database
    # user = User.query.filter_by(email=email).first()
    # if user is None:
    #     user = User(
    #         firstName=email.split('@')[0],
    #         email=email,
    #         is_oauth=True,
    #         is_verified=True,
    #         send_email_authorized=False
    #     )
    #     db.session.add(user)
    #     flash(f"Account created for email: {email}", "success")

    # # log the user in
    # user.last_login = datetime.now()
    # db.session.commit()
    # login_user(user)
    # flash(f"Logged In as {user.firstName}", "success")
    # return redirect(url_for('home'))

    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES["userInfo"], state=state)
    flow.redirect_uri = url_for('accounts.oauth2_callback', provider=provider, _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    credentials = credentials_to_dict(credentials)
    # print(credentials)

    if 'access_token' not in credentials:
        abort(401)
    
    
    response = requests.get(provider_data['userinfo']['url'], headers={
        'Authorization': 'Bearer ' + credentials["access_token"],
        'Accept': 'application/json',
    })

    if response.status_code != 200:
        abort(401)
    email = provider_data['userinfo']['email'](response.json())
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
            return redirect(url_for("home"))
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
    return redirect(url_for('home'))



@accounts_bp.route("/authorize/sendmessage/<provider>")
@login_required
def authorize_send_message(provider):
    if current_user.is_anonymous:
        return redirect(url_for("accounts.login"))

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=[SCOPES["userInfo"], SCOPES["sendMail"]])
    flow.redirect_uri = url_for('accounts.verify_send_message', provider=provider, _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    session['state'] = state
    print("\n\n HELLO \n\n")
    return redirect(authorization_url)


@accounts_bp.route("/callback/verifySentMessage/<provider>")
@login_required
def verify_send_message(provider):
    if current_user.is_anonymous:
        return redirect(url_for("accounts.login"))
    

    provider_data = app.config['OAUTH2_PROVIDERS'].get(provider)
    if provider_data is None:
        abort(404)

    # if there was an authentication error, flash the error messages and exit
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('home'))
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES["sendMail"], state=state)
    flow.redirect_uri = url_for('accounts.verify_send_message', provider=provider, _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    credentials = credentials_to_dict(credentials)
    print(credentials)
    
    if provider_data["scopes"]["sendmessage"] in credentials["granted_scopes"]:
        response = requests.get(provider_data['userinfo']['url'], headers={
        'Authorization': 'Bearer ' + credentials["access_token"],
        'Accept': 'application/json',
        })

        if response.status_code != 200:
            abort(401)
        email = provider_data['userinfo']['email'](response.json())
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
    return redirect(url_for("home"))




# def test():
#     url = "https://oauth2.googleapis.com/token"
#     user = User.query.get(int(current_user.get_id()))
#     payload = {
#         "client_id": "73844032923-2dkfq7ml3m0547ckoqpr1osrmb01201b.apps.googleusercontent.com",
#         "client_secret": "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",
#         "refresh_token": user.oauth_refresh_token,
#         "grant_type": "refresh_token"
#     }

#     response = requests.post(url, data=payload)
        
#     print(response)
#     print(response.json())
#     return redirect(url_for("home"))


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
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)
    
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
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    authorization_response = request.url
    flow.redirect_uri = "http://localhost:5000/callback2"
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    print(credentials.to_json())
    #get_credentials(request, state)
    return redirect(url_for("home"))


# @accounts_bp.route("/t")
# @login_required
# def t():
#     credentials = get_credentials_for_user(int(current_user.get_id()))
#     return redirect(url_for("home"))


@accounts_bp.route("/scopes")
@login_required
def scopes():
    credentials = get_credentials_for_user(int(current_user.get_id()))
    url = "https://www.googleapis.com/oauth2/v1/tokeninfo"
    response = requests.get(url, params={"access_token": credentials.token})
    print(response.json())
    flash(response.json(), "success")
    # message = gmail_send_message(credentials=credentials)
    return redirect(url_for("home"))



def encrypt(key, content):
    if content:
        f = Fernet(key)
        return f.encrypt(bytes(content, encoding="utf-8"))
    return None


def decrypt(key, token):
    if token:
        f = Fernet(key)
        return str(f.decrypt(token), encoding="utf-8")
    return None


def get_credentials_for_user(UserId):
    user = User.query.get(UserId)
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)
    refresh_token = decrypt(user.secret_salt, user.oauth_refresh_token)
    # print(dir(flow))
    # print(refresh_token)
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=flow.client_config["token_uri"],
        client_id=flow.client_config["client_id"],
        client_secret=flow.client_config["client_secret"]
    )
    # print(credentials)
    #print(credentials.to_json())
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)

    print(credentials.to_json())
    return credentials