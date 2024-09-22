import logging
import requests
from flask import Blueprint, redirect, url_for, session, request
from config import IG_SECRET, RED_URI
from flask_login import login_required, current_user
from database_manager import DatabaseManager

database_manager = DatabaseManager()

mongo = database_manager.get_db()


instagram_bp = Blueprint('instagram', __name__)

def exchange_short_lived_token(short_lived_token):
    url = "https://graph.instagram.com/access_token"
    params = {
        'grant_type': 'ig_exchange_token',
        'client_secret': IG_SECRET,
        'short_lived_token': short_lived_token
    }

    response = requests.get(url, data=params)
    return response.json()

@instagram_bp.route('/login/instagram')
def login_instagram():
    logging.info("Redirecting user to Instagram login.")
    return redirect(
        f"https://www.instagram.com/oauth/authorize?client_id=1068378404891316&redirect_uri={RED_URI}&response_type=code&scope=instagram_basic"
    )

@instagram_bp.route('/auth/instagram/callback')
def instagram_callback():
    code = request.args.get('code')
    logging.info("Instagram callback initiated.")
    if code:
        try:
            access_token_response = requests.post(
                'https://api.instagram.com/oauth/access_token',
                data={
                    'client_id': '1068378404891316',
                    'client_secret': IG_SECRET,
                    'code': code,
                    'grant_type': "authorization_code",
                    "redirect_uri": RED_URI
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
            return "Authorization failed", 400

        except Exception as e:
            logging.exception("Exception occurred during Instagram callback: %s", e)
            return "Authorization failed", 500

    logging.warning("No code received during Instagram callback.")
    return "Authorization failed", 400
