import logging
from oauth2client.client import flow_from_clientsecrets, OAuth2Credentials
from oauth2client.client import FlowExchangeError
from apiclient.discovery import build
import httplib2
from apiclient import errors, discovery
from secrets_app.model import User
from flask_login import current_user
from secrets_app import db
import google_auth_oauthlib.flow

# ...


# Path to client_secrets.json which should contain a JSON document such as:
#   {
#     "web": {
#       "client_id": "[[YOUR_CLIENT_ID]]",
#       "client_secret": "[[YOUR_CLIENT_SECRET]]",
#       "redirect_uris": [],
#       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#       "token_uri": "https://accounts.google.com/o/oauth2/token"
#     }
#   }
CLIENT_SECRETS_FILE = 'client_secret.json'
REDIRECT_URI = 'http://localhost:5000/callback2'
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    # Add other requested scopes.
]

class GetCredentialsException(Exception):
    """Error raised when an error occurred while retrieving credentials.

    Attributes:
    authorization_url: Authorization URL to redirect the user to in order to
                    request offline access.
    """

    def __init__(self, authorization_url):
        """Construct a GetCredentialsException."""
        self.authorization_url = authorization_url


class CodeExchangeException(GetCredentialsException):
    """Error raised when a code exchange has failed."""
    pass


class NoRefreshTokenException(GetCredentialsException):
    """Error raised when no refresh token has been found."""
    pass


class NoUserIdException(Exception):
    """Error raised when no user ID could be retrieved."""
    pass

def get_stored_credentials(email_address):
    """Retrieved stored credentials for the provided user ID.

    Args:
    user_id: User's ID.
    Returns:
    Stored oauth2client.client.OAuth2Credentials if found, None otherwise.
    Raises:
    NotImplemented: This function has not been implemented.
    """
    # TODO: Implement this function to work with your database.
    #       To instantiate an OAuth2Credentials instance from a Json
    #       representation, use the oauth2client.client.Credentials.new_from_json
    #       class method.
    print(email_address)
    user = User.query.filter_by(email=email_address).first()
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, ' '.join(SCOPES))
    client_id = flow.client_id
    client_secret = flow.client_secret
    print(client_id)
    print(client_secret)
    credentials = OAuth2Credentials(
        access_token=None,  # set access_token to None since we use a refresh token
        client_id=flow.client_id,
        client_secret=client_secret,
        refresh_token=user.oauth_refresh_token,
        token_expiry=None,
        token_uri=flow.token_uri,
        user_agent=None,
        revoke_uri=flow.revoke_uri)

    return credentials.refresh(httplib2.Http())
    


def store_credentials(user_id, email, credentials):
    """Store OAuth 2.0 credentials in the application's database.

    This function stores the provided OAuth 2.0 credentials using the user ID as
    key.

    Args:
    user_id: User's ID.
    credentials: OAuth 2.0 credentials to store.
    Raises:
    NotImplemented: This function has not been implemented.
    """
    # TODO: Implement this function to work with your database.
    #       To retrieve a Json representation of the credentials instance, call the
    #       credentials.to_json() method.
    print("\n\n ---> store credentials \n\n")
    user = User.query.filter_by(email=email).first()
    print(credentials.to_json())
    user.oauth_refresh_token = credentials.refresh_token
    #db.session.commit()

def exchange_code(request, state):
    """Exchange an authorization code for OAuth 2.0 credentials.

    Args:
    authorization_code: Authorization code to exchange for OAuth 2.0
                        credentials.
    Returns:
    oauth2client.client.OAuth2Credentials instance.
    Raises:
    CodeExchangeException: an error occurred.
    """
    # flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, ' '.join(SCOPES))
    # authorization_url, state = flow.authorization_url(
    #     access_type='offline',
    #     include_granted_scopes='true')
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = REDIRECT_URI
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    print(credentials.refresh_token)
    try:
        credentials = flow.credentials
        print(credentials)
        print(credentials.to_json())
        return credentials
    except FlowExchangeError as error:
        logging.error('An error occurred: %s', error)
        raise CodeExchangeException(None)


def get_user_info(credentials):
    """Send a request to the UserInfo API to retrieve the user's information.

    Args:
    credentials: oauth2client.client.OAuth2Credentials instance to authorize the
                    request.
    Returns:
    User information as a dict.
    """
    user_info_service = build(
        serviceName='oauth2', version='v2',
        credentials=credentials)
    user_info = None
    try:
        user_info = user_info_service.userinfo().get().execute()
        return user_info
    except errors.HttpError as  e:
        logging.error('An error occurred: %s', e)
        if user_info and user_info.get('id'):
            return user_info
        else:
            raise NoUserIdException()


def get_authorization_url(email_address, state):
    """Retrieve the authorization URL.

    Args:
    email_address: User's e-mail address.
    state: State for the authorization URL.
    Returns:
    Authorization URL to redirect the user to.
    """
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)
    
    flow.redirect_url = REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    return authorization_url


def get_credentials(authorization_code, state):
    """Retrieve credentials using the provided authorization code.

    This function exchanges the authorization code for an access token and queries
    the UserInfo API to retrieve the user's e-mail address.
    If a refresh token has been retrieved along with an access token, it is stored
    in the application database using the user's e-mail address as key.
    If no refresh token has been retrieved, the function checks in the application
    database for one and returns it if found or raises a NoRefreshTokenException
    with the authorization URL to redirect the user to.

    Args:
    authorization_code: Authorization code to use to retrieve an access token.
    state: State to set to the authorization URL in case of error.
    Returns:
    oauth2client.client.OAuth2Credentials instance containing an access and
    refresh token.
    Raises:
    CodeExchangeError: Could not exchange the authorization code.
    NoRefreshTokenException: No refresh token could be retrieved from the
                                available sources.
    """
    email_address = 'ravilladhaneesh@gmail.com'
    try:
        print("\n\n credentials = echange_code() ---> \n\n")
        credentials = exchange_code(authorization_code, state)
        print("\n\n ---> \n\n")
        user_info = get_user_info(credentials)
        email_address = user_info.get('email')
        user_id = user_info.get('id')
        print(email_address, user_id)
        print(credentials)
        if credentials.refresh_token is not None:
            store_credentials(user_id, email_address, credentials)
            return credentials
        else:
            credentials = get_stored_credentials(email_address)
            if credentials and credentials.refresh_token is not None:
                return credentials
    except CodeExchangeException as  error:
        logging.error('An error occurred during code exchange.')
        # Drive apps should try to retrieve the user and credentials for the current
        # session.
        # If none is available, redirect the user to the authorization URL.
        error.authorization_url = get_authorization_url(email_address, state)
        raise error
    except NoUserIdException:
        logging.error('No user ID could be retrieved.')
        # No refresh token has been retrieved.
        authorization_url = get_authorization_url(email_address, state)
        raise NoRefreshTokenException(authorization_url)
