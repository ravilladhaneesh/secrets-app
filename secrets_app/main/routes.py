from flask import render_template, Blueprint, request

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    verification_alert_shown = request.args.get('verification_alert_shown', False)
    return render_template("home.html", title='home', verification_alert_shown=verification_alert_shown)
