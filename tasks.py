from celery import shared_task 
from time import sleep
from secrets_app import create_app
from secrets_app.model import User
from datetime import date
from secrets_app.accounts.routes import get_credentials_for_user
from secrets_app.accounts.mail_service import send_scheduled_email
from celery.schedules import crontab


flask_app = create_app()
celery_app = flask_app.extensions["celery"]
celery_app.conf.timezone = 'Asia/Kolkata'


import os
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

celery_app.conf.beat_schedule = {
    'add-every-morning': {
        'task': 'tasks.schedule_email',
        'schedule': crontab(hour=6, minute=00),
    },
    'send-mail-3-mins': {
        'task': 'tasks.schedule_email',
        'schedule': crontab(minute='*/3')
    },
    # 'send-mail-30-seconds':{
    #     'task': 'tasks.schedule_email',
    #     'schedule': 30.0,
    # }
    
}

@celery_app.task
def email_notification(userId):
    with flask_app.app_context():
        user = User.query.get(userId)
        secrets = user.secrets
        credentials = get_credentials_for_user(user.id)
        for secret in secrets:
            nominees_mail = [nominee.email_id for nominee in secret.nominees]
            mail = send_scheduled_email(user.firstName, ", ".join(nominees_mail), secret, credentials=credentials)
            if mail:
                print("Sent the mail successfully")


@celery_app.task
def schedule_email():
    with flask_app.app_context():
        users = User.query.all()
        print(users, "==================>\n\n")
        for user in users:
            print(user, "==================>\n\n")
            if True or (date.today() - user.last_login).days > user.required_login_per_days:
                if True or user.send_email_authorized:
                    email_notification.delay(user.id)