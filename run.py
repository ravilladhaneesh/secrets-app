from secrets_app import app
import os

if __name__ == "__main__":
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(host='0.0.0.0', debug=True)