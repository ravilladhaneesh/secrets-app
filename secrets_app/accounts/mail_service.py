import base64
from email.message import EmailMessage

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from flask import url_for
from secrets_app import app
from secrets_app.model import User


ROOT_USER_EMAIL = app.config["ROOT_EMAIL"]

def gmail_send_message(credentials):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  #creds, _ = google.auth.default()

  try:
    service = build("gmail", "v1", credentials=credentials)
    message = EmailMessage()

    message.set_content("This is automated draft mail")

    message["To"] = "ravilladhaneesh@gmail.com"
    #message["From"] = "ravilladhaneees@gmail.com"
    message["Subject"] = "Automated draft"

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = None
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f"service: {service.users().messages()}")
    print(f"Message {message['From']}")
    print(f"Message {message['To']}")
    # print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message



def send_otp_from_root_account(otp, email_to):
    rootUser = User.query.filter_by(email=ROOT_USER_EMAIL).first()
    try:
       from secrets_app.accounts.routes import get_credentials_for_user
    except ImportError as err:
       print("Import Error", err)
       raise ImportError
    credentials = get_credentials_for_user(rootUser.id)
    service = build("gmail", "v1", credentials=credentials)
    message = EmailMessage()

    message["To"] = email_to
    message["Subject"] = "Account Verification OTP"

    message.set_content(f"Your mail {email_to} has requested to verify with the app. Your verification OTP is: {otp}")
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    send_message = None
    try:
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
    except HttpError as err:
        print(f"An error occurred: {err}")
    return send_message


def send_scheduled_email(userName, to, secret, credentials):
  try:
    service = build("gmail", "v1", credentials=credentials)
    message = EmailMessage()
    html = f"""
      <html>
        <head></head>
        <body>
          <p>This is automated secrets mail sent from the secrets app by {userName}</p>
          <h4>{secret.fieldName}</h4>
          <p>{secret.fieldSecret}</p>
        </body>
      </html>

    """
    message.set_content(html, subtype='html')
    message["To"] = to
    message["Subject"] = "Automated Secrets"

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = None
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f"service: {service.users().messages()}")
    print(f"Message {message['From']}")
    print(f"Message {message['To']}")
    # print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message


def send_reset_email(user):
    token = user.get_reset_token()
    rootUser = User.query.filter_by(email=ROOT_USER_EMAIL).first()
    try:
       from secrets_app.accounts.routes import get_credentials_for_user
    except ImportError as err:
       print("Import Error", err)
       raise ImportError
    credentials = get_credentials_for_user(rootUser.id)
    service = build("gmail", "v1", credentials=credentials)
    message = EmailMessage()

    message["To"] = user.email
    message["subject"] = 'Password Reset Request'
    body = f'''To reset your password, visit the following link:
{url_for('accounts.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    message.set_content(body)
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    send_message = None
    try:
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
    except HttpError as err:
        print(f"An error occurred: {err}")
    return send_message