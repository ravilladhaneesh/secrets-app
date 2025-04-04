import threading
import time
import schedule
from datetime import datetime, date
from secrets_app import app
from secrets_app.model import User
from secrets_app.accounts.routes import get_credentials_for_user
from secrets_app.accounts.mail_service import send_scheduled_email

def send_email_to_user(userId):
    print("HI")
    with app.app_context():
        user = User.query.get(userId)
        secrets = user.secrets
        credentials = get_credentials_for_user(user.id)
        for secret in secrets:
            nominees_mail = [nominee.email_id for nominee in secret.nominees]
            for i in nominees_mail:
                print(i)
            mail = send_scheduled_email(user.firstName, ", ".join(nominees_mail), secret, credentials=credentials)
            if mail:
                print("Sent the mail successfully")

        


def create_user_thread(user, userName):
    thread = threading.Thread(target=send_email_to_user, args=[user.id], name=userName)
    thread.start()


def schedule_email():
    print("hello")
    with app.app_context():
        users = User.query.all()
        for user in users:
            print(user)
            if (date.today() - user.last_login).days > user.required_login_per_days:
                if user.send_email_authorized:
                    print("Authorized")
                    create_user_thread(user, user.firstName)


schedule.every().day.at("09:52").do(schedule_email)


def run_continuously(interval=1):
    """Continuously run, while executing pending jobs at each
    elapsed time interval.
    @return cease_continuous_run: threading. Event which can
    be set to cease continuous run. Please note that it is
    *intended behavior that run_continuously() does not run
    missed jobs*. For example, if you've registered a job that
    should run every minute and you set a continuous run
    interval of one hour then your job won't be run 60 times
    at each interval but only once.
    """
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            i = 0
            
            while not cease_continuous_run.is_set():
                print(f"Before schedule.run_pending {i} {threading.current_thread()} {threading.get_ident()}")
                
                schedule.run_pending()
                print(f"After schedule.run_pending {i} {threading.current_thread()} {threading.get_ident()}")
                time.sleep(0)
                print(f"After time.sleep {i} {threading.current_thread()} {threading.get_ident()}")
                time.sleep(10)
                i += 1

    continuous_thread = ScheduleThread(name='foo')
    continuous_thread.daemon = True
    continuous_thread.start()
    return cease_continuous_run

run_continuously(10)