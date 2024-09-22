from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_required
from logging.handlers import RotatingFileHandler
import os
import logging
from bson.objectid import ObjectId
from werkzeug.middleware.proxy_fix import ProxyFix

from database_manager import DatabaseManager
database_manager = DatabaseManager()

from config import Config

# Initialize app
app = Flask(__name__)

# Load configuration from Config class
app.config.from_object(Config)

# Environment variables take precedence
app.config['MONGO_URI'] = os.getenv('MONGO_URI', app.config['MONGO_URI'])
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config['SECRET_KEY'])
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', app.config['DEBUG'])

# Secure cookie settings
app.config['SESSION_COOKIE_SECURE'] = True  # Ensure cookies are sent over HTTPS
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protect against JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Mitigate CSRF attacks

# Initialize MongoDB
mongo = database_manager.get_db()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# User class
class User(UserMixin):
    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_id=str(user_data['_id']), email=user_data['email'])
    return None

# Setup logging
if not os.path.exists('logs'):
    os.mkdir('logs')
    
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')

# Middleware for handling reverse proxy setups (e.g., NGINX)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

# Blueprints (ensure they're correctly imported)
from instagram import instagram_bp
from facebook import facebook_bp
from auth import auth_bp
from settings import settings_bp

app.register_blueprint(instagram_bp)
app.register_blueprint(facebook_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(settings_bp)

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
