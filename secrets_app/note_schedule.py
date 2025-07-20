import base64
from email.message import EmailMessage

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from flask import url_for, current_app, render_template
from secrets_app.model import User

def send_scheduled_note_mail(userName, to, note, credentials):
  try:
    service = build("gmail", "v1", credentials=credentials)
    message = EmailMessage()
    altered_note = {
      'content': note.content,
      'from': (note.user_id)
    }
    html = render_template("note_mail_template.html", note_content=note.content)

    message.set_content(html, subtype='html')
    message["To"] = to
    message["Subject"] = f"Automated Notes - {note.title}"

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
