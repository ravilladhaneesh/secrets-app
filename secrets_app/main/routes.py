from flask import render_template, Blueprint, request

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    verification_alert_shown = request.args.get('verification_alert_shown', False)
    return render_template("home.html", title='home', verification_alert_shown=verification_alert_shown)

@main_bp.route("/privacy-policy", methods=["GET"])
def privacy_policy():
    return render_template("privacy_policy.html", title="Privacy Policy")

@main_bp.route("/terms-and-conditions", methods=["GET"])
def terms_and_conditions():
    return render_template("terms-and-conditions.html", title='terms-and-conditions')