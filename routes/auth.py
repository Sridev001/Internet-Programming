"""User authentication routes."""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from forms.auth_forms import LoginForm, RegistrationForm, ProfileForm
import logging
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_employee:
            return redirect(url_for('employee.dashboard'))
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            logger.info(f"User logged in successfully: {user.email}")
            
            # Redirect based on user type
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif user.is_employee:
                return redirect(url_for('employee.dashboard'))
            return redirect(request.args.get('next') or url_for('main.index'))
        
        flash('Invalid email or password', 'error')
        logger.warning(f"Failed login attempt for email: {form.email.data}")
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))

        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_admin=False
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user registered: {user.email}")
            login_user(user)
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering new user: {str(e)}")
            flash('An error occurred during registration', 'error')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    if current_user.is_admin:
        return redirect(url_for('admin_auth.admin_logout'))
    
    user_email = current_user.email
    logout_user()
    logger.info(f"User logged out: {user_email}")
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle user profile management."""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
        
    form = ProfileForm()
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name

    if form.validate_on_submit():
        try:
            if form.current_password.data:
                if not current_user.check_password(form.current_password.data):
                    flash('Current password is incorrect', 'error')
                    return redirect(url_for('auth.profile'))
                
                if form.new_password.data:
                    current_user.set_password(form.new_password.data)

            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            db.session.commit()
            flash('Profile updated successfully', 'success')
            logger.info(f"Profile updated for user: {current_user.email}")
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {str(e)}")
            flash('An error occurred while updating your profile', 'error')
            return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)
