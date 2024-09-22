import logging
import requests
from flask import Blueprint, redirect, request, jsonify, session
from config import APP_ID, APP_SECRET, REDIRECT_URI
from flask_login import login_required, current_user
from database_manager import DatabaseManager

database_manager = DatabaseManager()
mongo = database_manager.get_db()

facebook_bp = Blueprint('facebook', __name__)

@facebook_bp.route('/facebook/login')
@login_required
def facebook_login():
    fb_login_url = f"https://www.facebook.com/v20.0/dialog/oauth?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope=public_profile,email"
    logging.info("Redirecting user to Facebook login.")
    return redirect(fb_login_url)

@facebook_bp.route('/handle_fb_code', methods=["GET", "POST"])
@login_required
def handle_fb_code():
    code = request.json.get('code')

    if not code:
        logging.error("No code provided for Facebook login.")
        return jsonify({'success': False, 'error': 'No code provided'}), 400

    token_exchange_url = f'https://graph.facebook.com/v20.0/oauth/access_token?client_id={APP_ID}&client_secret={APP_SECRET}&code={code}'
    response = requests.get(token_exchange_url)
    token_data = response.json()

    if 'access_token' not in token_data:
        logging.error("Failed to retrieve Facebook access token: %s", token_data)
        return jsonify({'success': False, 'error': token_data.get('error', 'Unknown error')}), 400

    access_token = token_data['access_token']
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
            ig_info = get_instagram_accounts(page_id=page["id"], page_access_token=page["access_token"])
            if ig_info is not None:
                data["ig"] = ig_info

            user_pages.append(data)

            install_url = f'https://graph.facebook.com/v20.0/{page["id"]}/subscribed_apps'
            install_response = requests.post(install_url, params={'access_token': page['access_token'], 'subscribed_fields': 'feed'})

            if install_response.status_code == 200:
                logging.info(f'Successfully installed on page: {page["name"]}')
            else:
                logging.error(f'Failed to install on page: {page["name"]} - {install_response.text}')

        mongo.users.update_one(
            {'email': current_user.email},
            {'$addToSet': {'managed_pages': {'$each': user_pages}}}
        )

        return jsonify({'success': True, 'access_token': access_token, 'managed_pages': user_pages})
    
    except Exception as e:
        logging.exception("Exception occurred while handling Facebook code: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


def get_instagram_accounts(page_id, page_access_token):
    """Fetch Instagram accounts linked to a Facebook page."""
    instagram_url = f'https://graph.facebook.com/v20.0/{page_id}/instagram_accounts?access_token={page_access_token}&fields=username'
    response = requests.get(instagram_url)
    if response.status_code == 200:
        instagram_data = response.json()
        return instagram_data.get('data', [])
    else:
        logging.error(f"Failed to retrieve Instagram accounts for page {page_id}: {response.text}")
        return None
