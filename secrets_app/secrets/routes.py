from flask import render_template, url_for, request, redirect, flash, Blueprint
from secrets_app.secrets.forms import AddSecretsForm, AddNomineeForm
from secrets_app import db
from secrets_app.model import User, Secret, Nominee
from flask_login import current_user, login_required
from secrets_app.secrets.utils import encrypt_secret, decrypt_secret


secrets_bp = Blueprint("secrets", __name__)


dummy_secrets_data = [
    Secret(fieldName='field1', fieldSecret='secret1', user_id=1, nominees=[Nominee(name='Nominee1', email_id='nominee1@gmail.com'), Nominee(name='Nominee2', email_id='nominee2@gmail.com')]),
    Secret(fieldName='field2', fieldSecret='secret2', user_id=1, nominees=[Nominee(name='Nominee2', email_id='nominee2@gmail.com')]),
    Secret(fieldName='field3', fieldSecret='secret3', user_id=1, nominees=[Nominee(name='Nominee2', email_id='nominee2@gmail.com')])
]


# @secrets_bp.route("/nominees")
# @login_required
# def nominees():
#     return render_template("nominee.html", title='nominee')





# @secrets_bp.route("/addSecrets", methods=["GET", "POST"])
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


# @secrets_bp.route("/secrets",methods=["GET", "POST"])
# @login_required
# def secrets():
#     if not current_user.is_authenticated:
#         return redirect(url_for('accounts.login'))
#     userId = current_user.get_id()
#     user = User.query.get(int(userId))
#     form = AddSecretsForm()
#     secrets_data = []
#     print("hello")
#     print("\n\n\n")
#     for item in form:
#         print(item)
#     if form.validate_on_submit():
#         print("hai")
#         secret_name = form.name.data
#         secret_value = form.secret.data
#         nominees = []
#         for nominee in form.nominees.data:
#             nominee_obj = Nominee(name=nominee["nominee_name"], email_id=nominee["email_id"])
#             nominees.append(nominee_obj)
#         secret = Secret(fieldName=secret_name, fieldSecret=secret_value, nominees=nominees, user_id=int(userId))
#         print(secret)
#         db.session.add(secret)
#         db.session.commit()
#         flash("New Secret Added", "success")
#         secrets_data.append(secret)
#         return redirect(url_for('secrets.secrets'))
#     secrets_data.extend(dummy_secrets_data)
#     secrets = Secret.query.filter_by(user_id=int(userId))
#     for secret in secrets:
#         secrets_data.append(secret)
#     print(secrets_data)
#     for i in secrets_data:
#         print(i.fieldName)
#     return render_template("secrets.html", form=form, title='secrets', secrets=secrets_data)



@secrets_bp.route("/secrets", methods=["GET", "POST"])
@login_required
def secrets():
    if not current_user.is_authenticated:
        return redirect(url_for('accounts.login'))
    
    userId = current_user.get_id()
    user = User.query.get(int(userId))
    form = AddSecretsForm()
    secrets_data = []
    
    if request.method == "POST":
        if form.validate_on_submit():
            for nominee in form.nominees:
                print(nominee)
            secret_name = encrypt_secret(form.name.data, user.secret_salt)
            secret_value = encrypt_secret(form.secret.data, user.secret_salt)
            nominees = []

            for nominee in form.nominees.data:
                nominee_obj = Nominee(name=nominee["name"], email_id=nominee["email_id"])
                nominees.append(nominee_obj)

            secret = Secret(fieldName=secret_name, fieldSecret=secret_value, nominees=nominees, user_id=int(userId))
            db.session.add(secret)
            db.session.commit()
            flash("New Secret Added", "success")
            return redirect(url_for('secrets.secrets'))
        else:
            # If form is not valid, display the errors
            # print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in {field}: {error}', "danger")
            # flash("Form contains errors, please correct them.(Check if you have added duplicate email ids)", "danger")
            return redirect(url_for('secrets.secrets'))
    # Fetch user's secrets
    print("Fetching secrets for user:", userId)
    secrets = Secret.query.filter_by(user_id=int(userId)).all()
    secrets_dict = [secret.to_dict() for secret in secrets]
    decrypt_secret_list = []
    for secret in secrets_dict:
        decrypt_secret_list.append({key: decrypt_secret(secret[key], user.secret_salt) if key in ['fieldName', 'fieldSecret'] else value for key, value in secret.items()})    
    return render_template('secrets.html', secrets=decrypt_secret_list, form=form, title="Secrets List")


@secrets_bp.route("/deleteSecret/<int:secretId>", methods=["GET", "POST"])
@login_required
def delete_secret(secretId):
    if not current_user.is_authenticated:
        return redirect(url_for('accounts.login'))

    userId = current_user.get_id()
    user = User.query.get(int(userId))

    secret = Secret.query.get_or_404(secretId)
    if secret.user_id == user.id:
        db.session.delete(secret)
        db.session.commit()
        flash(f"Deleted the secret {secret.fieldName}", "success")
        return redirect(url_for('secrets.secrets'))
    flash("Invalid secret selected", "danger")
    return redirect(url_for('secrets.secrets'))


@secrets_bp.route("/editSecret/<int:secretId>", methods=["GET", "POST"])
@login_required
def edit_secret(secretId):
    if not current_user.is_authenticated:
        return redirect(url_for('accounts.login'))
    
    userId = current_user.get_id()
    user = User.query.get(int(userId))
    secret = Secret.query.get_or_404(secretId)
    if secret.user_id != user.id:
        flash("You do not have permission to edit this secret", "danger")
        return redirect(url_for('secrets.secrets'))
    form = AddSecretsForm()
    if form.validate_on_submit():
        print("hello")
        secret.fieldName = encrypt_secret(form.name.data, user.secret_salt)
        secret.fieldSecret = encrypt_secret(form.secret.data, user.secret_salt)
        for i in secret.nominees:
            db.session.delete(i)

        for nominee_form in form.nominees.data:
            new_nominee = Nominee(
                name=nominee_form["name"],
                email_id=nominee_form["email_id"]
            )
            db.session.add(new_nominee)
            secret.nominees.append(new_nominee)
        print("\n\n\n\n\n")

        db.session.add(secret)
        db.session.commit()
        flash("Secret updated successfully", "success")
        return redirect(url_for("secrets.secrets"))
    if request.method == "GET":
        form.name.data = decrypt_secret(secret.fieldName, user.secret_salt)
        # for nominee in secret.nominees:
        #     # nominee_form = AddNomineeForm()
        #     # nominee_form.name = nominee.name
        #     # nominee_form.email_id = nominee.email_id
        #     # form.nominees.append_entry(nominee_form)
        #     form.nominees.append_entry({
        #         'name': nominee.name,
        #         'email_id': nominee.email_id
        #     })
        #     print(nominee)

    return render_template('edit_secret.html', form=form, secret=secret, title="Edit Secret")

