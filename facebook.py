from flask import Blueprint, redirect, request, jsonify, session
from flask_login import login_required, current_user
import logging
import requests

# INTERNAL IMPORTS
from database_manager import DatabaseManager
from facebook_utils import get_short_token, install_to_app, ig_data
from config import Config

database_manager = DatabaseManager().get_instance()
mongo = database_manager.get_db()

config = Config()

facebook_bp = Blueprint('facebook', __name__)

@facebook_bp.route('/facebook/login')
@login_required
def facebook_login():
    fb_login_url = f"https://www.facebook.com/v20.0/dialog/oauth?client_id={config.FB_APP_ID}&redirect_uri={config.FB_REDIRECT_URI}&scope=public_profile,email"
    logging.info("Redirecting user to Facebook login.")
    return redirect(fb_login_url)

@facebook_bp.route('/handle_fb_code', methods=["GET", "POST"])
@login_required
def handle_fb_code():
    code = request.json.get('code')

    if not code:
        logging.error("No code provided for Facebook login.")
        return jsonify({'success': False, 'error': 'No code provided'}), 400

    access_token = get_short_token(code)

    session['fb_access_token'] = access_token

    mongo.users.update_one({'email': current_user.email}, {'$set': {'fb_access_token': access_token}})

    try:
        pages_url = f'https://graph.facebook.com/v20.0/me/accounts?access_token={access_token}'
        pages_response = requests.get(pages_url)
        pages_data = pages_response.json()

        user_pages = []
        for page in pages_data.get('data', []):
            data = {
                'page_id': page['id'],
                'page_name': page['name'],
                'page_access_token': page['access_token']
            }

            ig_data(page, data)

            user_pages.append(data)

            install_to_app(page)

        mongo.users.update_one(
            {'email': current_user.email},
            {'$addToSet': {'managed_pages': {'$each': user_pages}}}
        )

        return jsonify({'success': True, 'access_token': access_token, 'managed_pages': user_pages})
    
    except Exception as e:
        logging.exception("Exception occurred while handling Facebook code: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500