import logging
from flask import Blueprint, request, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import User

from database_manager import DatabaseManager

database_manager = DatabaseManager().get_instance()

mongo = database_manager.get_db()
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/logout')
@login_required
def logout():
    logging.info("User %s logged out.", current_user.email)
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        logging.info("User attempting to register with email: %s", email)
        hashed_password = generate_password_hash(password)
        mongo.users.insert_one({'email': email, 'password': hashed_password})
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = mongo.users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            login_user(User(user_id=user['_id'], email=user['email']), force=True)
            logging.info("User %s logged in successfully.", email)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        logging.warning("Invalid login attempt for email: %s", email)
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')
