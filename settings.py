from datetime import datetime
from flask import Blueprint, redirect, url_for, render_template, request, flash
from flask_login import login_required, current_user
import logging
from bson.objectid import ObjectId
from pymongo import MongoClient
from config import MONGO_BASE

db = MongoClient(f'mongodb://{MONGO_BASE}/HaSpDeDash')
client = db["HaSpDeDash"]
# Define the blueprint
settings_bp = Blueprint('settings', __name__, url_prefix="/settings/")

# Route to moderation panel
@settings_bp.route("/")
@login_required
def index():
    # Fetch the user document with the 'managed_pages' field
    user_data = client.users.find_one({'email': current_user.email})

    # Ensure user_data is retrieved
    if not user_data:
        flash("Käyttäjää ei löytynyt.", "error")
        return redirect(url_for('some_other_route'))  # Handle non-existent user case
    
    # Safely get 'managed_pages' from user_data, default to empty list if None
    pages = user_data.get("managed_pages", [])
    igs_2 = user_data.get("managed_igs", [])
    pages_ = []
    pages_id = set()  # Set to track unique page IDs
    IGs = []
    IG_ids = set()

    for page in pages:
        # Initialize an empty config for each page if not present
        page["config"] = page.get("config", {})

        if page.get("ig"):
            for ig in page.get("ig", []):
                if not ig.get("id") in IG_ids:
                    IGs.append({"id": ig.get("id"), "name": ig.get("username"), "config": ig.get("config", {})})
                    IG_ids.add(ig.get("id"))

        # Add page if its ID is not already in pages_id
        if page.get("page_id") not in pages_id:
            pages_.append(page)
            pages_id.add(page.get("page_id"))
        else:
            logging.info("Not adding duplicate page: %s", page.get("page_id"))
    
    for ig in igs_2:
        if not ig.get("id") in IG_ids:
            IGs.append({"id": ig.get("id"), "name": ig.get("username"), "config": ig.get("config", {})})
            IG_ids.add(ig.get("id"))

    # Pass the modified 'pages_' list to the template
    return render_template("settings.html", pages=pages_, igs=IGs)

# Route to update page configuration
@settings_bp.route('/update_config/<page_id>', methods=['POST'])
@login_required
def update_config(page_id):
    # Fetch new configuration from the form data
    profanity_filter = request.form.get('profanity_filter') == 'on'
    detection_threshold = request.form.get('detection_threshold', 65)
    human_review = request.form.get('human_review') == 'on'

    try:
        detection_threshold = int(detection_threshold)
    except ValueError:
        flash("Havaintokynnys on annettava numerona.", "error")
        return redirect(url_for('moderation_bp.moderation'))

    # Input validation
    if detection_threshold < 0 or detection_threshold > 100:
        flash("Havaintokynnys täytyy olla välillä 0-100.", "error")
        return redirect(url_for('moderation_bp.moderation'))

    # Update the page's configuration in the user's document
    update_result = client.users.update_one(
        {
            'email': current_user.email,
            'managed_pages.page_id': page_id
        },
        {
            '$set': {
                'managed_pages.$.config.profanity_filter': profanity_filter,
                'managed_pages.$.config.detection_threshold': detection_threshold,
                'managed_pages.$.config.human_review': human_review
            }
        }
    )

    if update_result.matched_count == 0:
        flash("Sivua ei löytynyt.", "error")
    else:
        flash("Asetukset tallennettiin onnistuneesti.", "success")

    # Redirect back to the moderation panel
    return redirect(url_for('moderation_bp.moderation'))


@settings_bp.route('/update_ig_config/<ig_id>', methods=['POST'])
@login_required
def update_ig_config(ig_id):
    # Fetch new configuration from the form data
    profanity_filter = request.form.get('profanity_filter_ig') == 'on'
    detection_threshold = request.form.get('detection_threshold_ig', 65)
    human_review = request.form.get('human_review_ig') == 'on'

    try:
        detection_threshold = int(detection_threshold)
    except ValueError:
        flash("Havaintokynnys on annettava numerona.", "error")
        return redirect(url_for('moderation_bp.moderation'))

    # Input validation
    if detection_threshold < 0 or detection_threshold > 100:
        flash("Havaintokynnys täytyy olla välillä 0-100.", "error")
        return redirect(url_for('moderation_bp.moderation'))

    # Update the IG's configuration within the specific page
    update_result = client.users.update_one(
        {
            'email': current_user.email,
            'managed_pages.ig.id': ig_id
        },
        {
            '$set': {
                'managed_pages.$.ig.$[ig].config.profanity_filter': profanity_filter,
                'managed_pages.$.ig.$[ig].config.detection_threshold': detection_threshold,
                'managed_pages.$.ig.$[ig].config.human_review': human_review
            }
        },
        array_filters=[{'ig.id': ig_id}]  # This ensures we target the correct IG within the page
    )

    if update_result.matched_count == 0:
        flash("Instagram-tili ei löytynyt.", "error")
    else:
        flash("Instagram-asetukset tallennettiin onnistuneesti.", "success")

    # Redirect back to the moderation panel
    return redirect(url_for('moderation_bp.moderation'))
