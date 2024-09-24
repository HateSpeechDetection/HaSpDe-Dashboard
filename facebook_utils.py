import requests
from facebook import logging
from flask import jsonify
from config import Config
config = Config()

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

def get_short_token(code):
    token_exchange_url = f'https://graph.facebook.com/v20.0/oauth/access_token?client_id={config.FB_APP_ID}&client_secret={config.FB_APP_SECRET}&code={code}'
    response = requests.get(token_exchange_url)
    token_data = response.json()

    if 'access_token' not in token_data:
        logging.error("Failed to retrieve Facebook access token: %s", token_data)
        return jsonify({'success': False, 'error': token_data.get('error', 'Unknown error')}), 400

    access_token = token_data['access_token']

    return access_token


def install_to_app(page):
    install_url = f'https://graph.facebook.com/v20.0/{page["id"]}/subscribed_apps'
    install_response = requests.post(install_url, params={'access_token': page['access_token'], 'subscribed_fields': 'feed'})

    if install_response.status_code == 200:
        logging.info(f'Successfully installed on page: {page["name"]}')
    else:
        logging.error(f'Failed to install on page: {page["name"]} - {install_response.text}')

def ig_data(page, data):
    ig_info = get_instagram_accounts(page_id=page["id"], page_access_token=page["access_token"])
    if ig_info is not None:
        data["ig"] = ig_info
