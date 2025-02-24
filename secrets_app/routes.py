from flask import render_template, url_for, request, redirect, flash
from secrets_app.forms import UserLoginForm, UserRegistrationForm, UserUpdateForm, AddSecretsForm
from secrets_app import app, db, bcrypt, login_manager
from secrets_app.model import User, Secret, Nominee
from flask_login import login_user, current_user, logout_user, login_required


dummy_secrets_data = [
    Secret(fieldName='field1', fieldSecret='secret1', user_id=1, nominees=[Nominee(name='Nominee1', email_id='nominee1@gmail.com'), Nominee(name='Nominee2', email_id='nominee2@gmail.com')]),
    Secret(fieldName='field2', fieldSecret='secret2', user_id=1, nominees=[Nominee(name='Nominee2', email_id='nominee2@gmail.com')]),
    Secret(fieldName='field3', fieldSecret='secret3', user_id=1, nominees=[Nominee(name='Nominee2', email_id='nominee2@gmail.com')])
]


@app.route("/")
def home():
    return render_template("home.html", title='home')



# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     form = UserRegistrationForm()
#     if request.method == "POST":
#         print(form.validate_on_submit() == True)
#         if form.validate_on_submit():
#             hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
#             user = User(firstName=form.firstName.data, lastName=form.lastName.data, email=form.email.data, password=hashed_pw)
#             db.session.add(user)
#             db.session.commit()
#             flash(f'Account created for email {form.email.data}!.You can now login in.', 'success')
#             return redirect(url_for('login'))
#         else:
#             flash(f'Error Validating the form', 'danger')
#     return render_template("register.html", form=form, title='register')


# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     form = UserLoginForm()
#     if request.method == "POST":
#         if form.validate_on_submit():
#             user = User.query.filter_by(email=form.email.data).first()
#             if user and bcrypt.check_password_hash(user.password, form.password.data):
#                 login_user(user, remember=False)
#                 next = request.args.get("next")
#                 flash(f'Logged In as {user.firstName}', 'success')
#                 return redirect(next) if next else redirect(url_for('home'))
#         flash('Login failed. Please check username and password', 'danger')
#     return render_template("login.html", form=form, title='login')


# @app.route("/logout", methods=["GET"])
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('login'))


@app.route("/nominees")
@login_required
def nominees():
    return render_template("nominee.html", title='nominee')


# @app.route("/addSecrets", methods=["GET", "POST"])
# @login_required
# def addSecrets():
#     userId = int(current_user.get_id())
#     user = User.query.get(userId)
#     form = AddSecretsForm()
#     if form.validate_on_submit():
#         secret_name = form.name.data
#         secret_value = form.value.data
#         for nominee in form.nominees.data:
#             print(nominee.name.data)
#             print(nominee.email.data)
#     return render_template('secret.html', form=form)


@app.route("/secrets",methods=["GET", "POST"])
@login_required
def secrets():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    userId = current_user.get_id()
    user = User.query.get(int(userId))
    form = AddSecretsForm()
    secrets_data = []
    if form.validate_on_submit():
        secret_name = form.name.data
        secret_value = form.secret.data
        nominees = []
        for nominee in form.nominees.data:
            nominee_obj = Nominee(name=nominee["nominee_name"], email_id=nominee["email_id"])
            nominees.append(nominee_obj)
        secret = Secret(fieldName=secret_name, fieldSecret=secret_value, nominees=nominees, user_id=int(userId))
        db.session.add(secret)
        db.session.commit()
        flash("New Secret Added", "success")
        secrets_data.append(secret)
        return redirect(url_for('secrets'))
    secrets_data.extend(dummy_secrets_data)
    secrets = Secret.query.filter_by(user_id=int(userId))
    for secret in secrets:
        secrets_data.append(secret)
    print(secrets_data)
    for i in secrets_data:
        print(i.fieldName)
    return render_template("secret.html", form=form, title='secrets', secrets=secrets_data)


# @app.route("/account", methods=["GET", "POST"])
# @login_required
# def account():
#     form = UserUpdateForm()
#     userId = int(current_user.get_id())
#     user = User.query.get(userId)
#     if request.method == "POST":
        
#         for field, errorMessage in form.errors.items():
#             print(field, errorMessage)
#         if user and form.validate_on_submit():
#             user.firstName = form.firstName.data
#             user.lastName = form.lastName.data
#             user.required_login_per_days = form.required_login_per_days.data
#             print(user.firstName, user.lastName, user.required_login_per_days)
#             db.session.commit()
#             flash("User Details Updated", 'success')
#             return redirect(url_for('account'))
#         print(form.errors)
#         print("Hi")
#     elif request.method == "GET":
#         form.firstName.data = current_user.firstName
#         form.lastName.data = current_user.lastName
#         form.required_login_per_days.data = current_user.required_login_per_days
#     return render_template('account.html', form=form)



