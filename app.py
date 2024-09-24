from flask import Flask, render_template
from flask_login import login_required
from bson.objectid import ObjectId
from werkzeug.middleware.proxy_fix import ProxyFix
from status_package import Status

# Internal imports
from config import Config
from models import User
from utils import initialize_logging, initialize_blueprints, initialize_login_manager, initialize_database_manager, initialize_config

# Initialize app
app = Flask(__name__)

# Load configuration from Config class
app.config.from_object(Config())
initialize_config(app)

# Initialize the status checker
status = Status(app, mongo_uri=app.config['MONGO_URI'])

login_manager = initialize_login_manager(app)
initialize_logging(app)
database_manager, mongo = initialize_database_manager()
initialize_blueprints(app)

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_id=str(user_data['_id']), email=user_data['email'])
    return None

# Middleware for handling reverse proxy setups (e.g., NGINX)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

# Default route
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Error handling
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server error: {error}')
    return render_template('500.html'), 500

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
