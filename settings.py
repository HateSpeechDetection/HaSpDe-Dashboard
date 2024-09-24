from flask import Blueprint, redirect, url_for, render_template, request, flash
from flask_login import login_required, current_user
import logging
from database_manager import DatabaseManager

db_manager = DatabaseManager().get_instance()

client = db_manager.get_db()

# Define the blueprint
settings_bp = Blueprint('settings', __name__, url_prefix="/settings/")

# Route to moderation panel
@settings_bp.route("/")
@login_required
def index():
    # Fetch the user's document by email, ensuring 'managed_pages' and 'managed_igs' exist
    user_data = client.users.find_one({'email': current_user.email})

    if not user_data:
        flash("Käyttäjää ei löytynyt.", "error")
        return redirect("index")  # FIXME: Handle non-existent user case properly

    # Safely extract 'managed_pages' and 'managed_igs', defaulting to empty lists if missing
    pages = user_data.get("managed_pages", [])
    igs_2 = user_data.get("managed_igs", [])
    
    pages_ = []
    IGs = []
    pages_id = set()  # Set to track unique page IDs
    IG_ids = set()    # Set to track unique Instagram IDs

    # Process managed Facebook pages
    for page in pages:
        page["config"] = page.get("config", {})  # Ensure 'config' exists

        # Process linked Instagram accounts, ensuring no duplicates
        for ig in page.get("ig", []):
            _id = ig.get("id", None)
            if _id not in IG_ids and not _id is None:
                IGs.append({"id": ig["id"], "name": ig.get("username"), "config": ig.get("config", {})})
                IG_ids.add(ig["id"])

        # Add unique pages to the list
        if page["page_id"] not in pages_id:
            pages_.append(page)
            pages_id.add(page["page_id"])
        else:
            logging.info(f"Duplicate page skipped: {page['page_id']}")

    # Process standalone Instagram accounts and avoid duplicates
    for ig in igs_2:
        if ig["user_id"] not in IG_ids:
            IGs.append({"id": ig["user_id"], "name": ig.get("username"), "config": ig.get("config", {})})
            IG_ids.add(ig["user_id"])

    # Render the template with the cleaned-up list of pages and Instagram accounts
    return render_template("settings.html", pages=pages_, igs=IGs)
# Route to update page configuration
@settings_bp.route('/update_config/<page_id>', methods=['POST'])
@login_required
def update_config(page_id):
    # Fetch new configuration from form data
    profanity_filter = request.form.get('profanity_filter') == 'on'
    detection_threshold = request.form.get('detection_threshold', 65)
    human_review = request.form.get('human_review') == 'on'

    # Convert detection_threshold to an integer, or flash an error if it's not valid
    try:
        detection_threshold = int(detection_threshold)
    except ValueError:
        flash("Havaintokynnys on annettava numerona.", "error")
        return redirect(url_for('settings.index'))

    # Ensure detection_threshold is within the valid range of 0-100
    if not (0 <= detection_threshold <= 100):
        flash("Havaintokynnys täytyy olla välillä 0-100.", "error")
        return redirect(url_for('settings.index'))

    # Update the page's configuration in the user's document
    update_result = client.users.update_one(
        {
            'email': current_user.email,  # Match the current user's email
            'managed_pages.page_id': page_id  # Match the specific page by ID
        },
        {
            # Update the specific page's configuration
            '$set': {
                'managed_pages.$.config.profanity_filter': profanity_filter,
                'managed_pages.$.config.detection_threshold': detection_threshold,
                'managed_pages.$.config.human_review': human_review
            }
        }
    )

    # Check if the page was found and updated
    if update_result.matched_count == 0:
        flash("Sivua ei löytynyt.", "error")  # No page matched
    else:
        flash("Asetukset tallennettiin onnistuneesti.", "success")  # Successful update

    # Redirect back to the moderation panel
    return redirect(url_for('settings.index'))

# Route to update Instagram (IG) configuration
@settings_bp.route('/update_ig_config/<ig_id>', methods=['POST'])
@login_required
def update_ig_config(ig_id):
    # Fetch new configuration from the form data
    profanity_filter, detection_threshold, human_review = get_ig_config_form()

    # Convert detection_threshold to an integer and handle conversion error
    try:
        detection_threshold = int(detection_threshold)
    except ValueError:
        flash("Havaintokynnys on annettava numerona.", "error")
        return redirect(url_for('settings.index'))

    # Validate detection_threshold to be in the range 0-100
    if not (0 <= detection_threshold <= 100):
        flash("Havaintokynnys täytyy olla välillä 0-100.", "error")
        return redirect(url_for('settings.index'))

    # Update the IG's configuration for the specific Instagram account within the user's pages
    update_result = client.users.update_one(
        {
            'email': current_user.email,  # Ensure the query is for the current user's email
            'managed_pages.ig.id': ig_id   # Match the Instagram account by ID
        },
        {
            # Update the configuration for the matched Instagram account
            '$set': {
                'managed_pages.$.ig.$[ig].config.profanity_filter': profanity_filter,
                'managed_pages.$.ig.$[ig].config.detection_threshold': detection_threshold,
                'managed_pages.$.ig.$[ig].config.human_review': human_review
            }
        },
        array_filters=[{'ig.id': ig_id}]  # Use array filters to target the correct IG within managed_pages
    )

    # Check if the Instagram account was found and updated
    if update_result.matched_count == 0:
        flash("Instagram-tili ei löytynyt.", "error")  # No IG account matched
    else:
        flash("Instagram-asetukset tallennettiin onnistuneesti.", "success")  # Successful update

    # Redirect back to the moderation panel
    return redirect(url_for('settings.index'))


def get_ig_config_form():
    profanity_filter = request.form.get('profanity_filter_ig') == 'on'
    detection_threshold = request.form.get('detection_threshold_ig', 65)
    human_review = request.form.get('human_review_ig') == 'on'
    return profanity_filter,detection_threshold,human_review
