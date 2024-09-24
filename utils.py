from logging.handlers import RotatingFileHandler
import os
import logging

from flask_login import LoginManager

from database_manager import DatabaseManager

from pymongo.database import Database

from typing import Tuple


from instagram import instagram_bp
from facebook import facebook_bp
from auth import auth_bp
from settings import settings_bp

def initialize_logging(app):
    # Setup logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

def initialize_blueprints(app):
    app.register_blueprint(instagram_bp)
    app.register_blueprint(facebook_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)

def initialize_login_manager(app):
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'


    return login_manager

def initialize_database_manager() -> Tuple['DatabaseManager', 'Database']:
    # Initialize DB manager
    database_manager = DatabaseManager().get_instance()

    # Initialize MongoDB
    mongo = database_manager.get_db()

    return database_manager, mongo

def initialize_config(app):
    # Environment variables take precedence
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', app.config['MONGO_URI'])
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config['SECRET_KEY'])
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', app.config['DEBUG'])

    # Secure cookie settings
    app.config['SESSION_COOKIE_SECURE'] = True  # Ensure cookies are sent over HTTPS
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protect against JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Mitigate CSRF attacks

