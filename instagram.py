import logging
import requests
from flask import Blueprint, redirect, url_for, session, request, abort
from config import Config
from flask_login import current_user
from database_manager import DatabaseManager

# Initialize the database manager and MongoDB connection
database_manager = DatabaseManager().get_instance()
mongo = database_manager.get_db()

# Load configuration
config = Config()

# Create a Flask Blueprint for Instagram functionality
instagram_bp = Blueprint('instagram', __name__)

# Define a warning message
warning_message = (
    "# IMPORTANT: READ THIS BEFORE WASTING YOUR TIME!\n"
    "# WARNING: The functionality in this module is currently NON-FUNCTIONAL due to ongoing issues with META Ltd.\n"
    "# This serves as a critical warning to anyone attempting to implement or troubleshoot this code.\n"
    "# The significant time and effort invested in resolving these issues—200 hours over 20-25 September 2024—have yielded no success.\n"
    "# Proceed at your own risk, and consider seeking alternatives before diving into a frustrating experience!\n"
    "# - botsarefuture"
)

@instagram_bp.route('/login/instagram')
def login_instagram():
    logging.info("Redirecting user to Instagram login.")
    abort(501)
    return warning_message  # Return the warning message before handling

@instagram_bp.route('/auth/instagram/callback')
def instagram_callback():
    logging.info("Instagram callback initiated.")
    abort(501)

    return warning_message  # Return the warning message before handling

    # Note: The following code will never execute due to the early return.
    code = request.args.get('code')
    if code:
        try:
            access_token_response = requests.post(
                'https://api.instagram.com/oauth/access_token',
                data={
                    'client_id': config.IG_CLIENT_ID,
                    'client_secret': config.IG_APP_SECRET,
                    'code': code,
                    'grant_type': "authorization_code",
                    "redirect_uri": config.FB_REDIRECT_URI  # Corrected variable name
                }
            )
            access_token_info = access_token_response.json()

            if 'access_token' in access_token_info:
                logging.info("Access token retrieved successfully.")
                short_lived_token = access_token_info['access_token']
                session['access_token'] = short_lived_token

                long_lived_token_info = exchange_short_lived_token(short_lived_token)
                if 'access_token' in long_lived_token_info:
                    long_lived_token = long_lived_token_info['access_token']
                    session['long_lived_access_token'] = long_lived_token

                    user_info_response = requests.get(
                        f'https://graph.instagram.com/me?fields=id,username&access_token={long_lived_token}'
                    )
                    user_info = user_info_response.json()

                    mongo.users.update_one(
                        {'email': current_user.email},
                        {
                            '$addToSet': {
                                'managed_igs': {
                                    'user_id': user_info['id'],
                                    'username': user_info['username'],
                                    'access_token': long_lived_token
                                }
                            }
                        }
                    )
                    return redirect(url_for('index'))

            logging.error("Failed to retrieve access token: %s", access_token_info)
            return warning_message  # Return the warning message if access token retrieval fails

        except Exception as e:
            logging.exception("Exception occurred during Instagram callback: %s", e)
            return warning_message  # Return the warning message if an exception occurs

    logging.warning("No code received during Instagram callback.")
    return warning_message  # Return the warning message if no code is received
