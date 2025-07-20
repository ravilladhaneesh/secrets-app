from celery import shared_task 
from time import sleep
from secrets_app import create_app
from secrets_app.model import User
from datetime import date
from secrets_app.accounts.routes import get_credentials_for_user
from secrets_app.accounts.mail_service import send_scheduled_email
from secrets_app.secrets.utils import decrypt_secret
from celery.schedules import crontab
import os
import boto3
from datetime import datetime

from secrets_app.note_schedule import send_scheduled_note_mail

import shutil



flask_app = create_app()
celery_app = flask_app.extensions["celery"]
celery_app.conf.timezone = 'Asia/Kolkata'


import os
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

celery_app.conf.beat_schedule = {
    'mail-every-morning': {
        'task': 'tasks.schedule_email',
        'schedule': crontab(hour=6, minute=00),
    },
    'backup-database-every-day': {
        'task': 'tasks.backup_database',
        'schedule': crontab(hour=1, minute=00),
    },
    # 'mail-every-evening': {
    #     'task': 'tasks.schedule_email',
    #     'schedule': crontab(hour=17, minute=45),
    # },
    # 'mail-note-every-morning': {
    #     'task': 'tasks.schedule_note_email',
    #     'schedule': crontab(hour=6, minute=00),
    # },
    # 'mail-note-every-evening': {
    #     'task': 'tasks.schedule_note_email',
    #     'schedule': crontab(hour=18, minute=00),
    # },
    # 'send-mail-3-mins': {
    #     'task': 'tasks.schedule_email',
    #     'schedule': crontab(minute='*/3')
    # },
    # 'send-mail-3-mins-notes': {
    #     'task': 'tasks.schedule_note_email',
    #     'schedule': crontab(minute='*/1')
    # },
    # 'send-mail-30-seconds':{
    #     'task': 'tasks.schedule_email',
    #     'schedule': crontab(minute='*/1')
    # }
    
}

@celery_app.task
def email_notification(userId):
    with flask_app.app_context():
        user = User.query.get(userId)
        secrets = user.secrets
        notes = user.notes
        credentials = get_credentials_for_user(user.id)
        send_notification_limit = (date.today() - user.last_login).days - user.required_login_per_days <= 2
        print("Sending email notification for user:", user.firstName, user.email)

        print("Last login days: ", (date.today() - user.last_login).days)
        print("Required login per days:", user.required_login_per_days)

        print("send_notification_limit", send_notification_limit)
        print((date.today() - user.last_login).days > user.required_login_per_days)
        if (date.today() - user.last_login).days > user.required_login_per_days and send_notification_limit:
            for secret in secrets:
                nominees_mail = [nominee.email_id for nominee in secret.nominees]
                secret.fieldSecret = decrypt_secret(secret.fieldSecret, user.secret_salt)
                secret.fieldName = decrypt_secret(secret.fieldName, user.secret_salt)
                mail = send_scheduled_email(user.firstName, ", ".join(nominees_mail), secret, credentials=credentials)
                if mail:
                    print("Sent secrets mail successfully")
        for note in notes:
            print(note.send_date, "==================>\n\n", note.send_date.today())
            if note.send_date and note.send_date == date.today():
                receivers = []
                print("Sending note email for:", note.title)
                if note.to_self:
                    receivers.append(user.email)
                else:
                    receivers = [note.email_id for note in note.receivers]
                mail = send_scheduled_note_mail(user.firstName, ", ".join(receivers), note, credentials=credentials)
                if mail:
                    print("Sent notes mail successfully")


@celery_app.task
def schedule_email():
    with flask_app.app_context():
        users = User.query.all()
        print(users, "==================>\n\n")
        for user in users:
            print(user, "==================>\n\n")
            if user.send_email_authorized:
                email_notification.delay(user.id)


# @celery_app.task
# def schedule_note_email():
#     with flask_app.app_context():
#         users = User.query.all()
#         for user in users:
#             if  user.send_email_authorized:
#                     email_notification.delay(user.id)


def copy_db_file(src, dest):
    if os.path.exists(src):
        shutil.copy(src, dest)
        print(f"Database copied from {src} to {dest}")
    else:
        print(f"Source database file {src} does not exist.")


@celery_app.task
def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"/tmp/app_backup_{timestamp}.db"
    
    # Ensure the backup directory exists
    os.makedirs(os.path.dirname(backup_filename), exist_ok=True)
    # Path to the SQLite DB (adjust based on your app's path)
    
    db_path = os.getenv("DB_PATH", "/app/instance/site.db")
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist. Skipping backup.")
        return
    
    copy_db_file(db_path, backup_filename)
    
    
    # Step 2: Upload the backup to S3 using Boto3
    s3_client = boto3.client('s3')
    s3_bucket = 'securethem-bucket'
    s3_key = f"sqlite_backups/app_backup_{timestamp}.db"
    
    try:
        # Upload the file to S3
        s3_client.upload_file(backup_filename, s3_bucket, s3_key)
        print(f"Backup successful: {s3_key}")
    except Exception as e:
        print(f"Backup failed: {e}")
    
    # Step 3: Clean up the local backup file
    os.remove(backup_filename)
