"""Admin authentication routes."""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User
from forms.admin_forms import AdminLoginForm
import logging
from datetime import datetime

admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/admin/auth')
logger = logging.getLogger(__name__)

@admin_auth_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Handle admin login."""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_admin and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            session['admin_access'] = True
            session['last_seen'] = datetime.utcnow().isoformat()
            logger.info(f"Admin logged in successfully: {user.email}")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
            logger.warning(f"Failed admin login attempt for email: {form.email.data}")
    
    return render_template('admin/auth/login.html', form=form)

@admin_auth_bp.route('/logout')
@login_required
def admin_logout():
    """Handle admin logout."""
    if current_user.is_admin:
        session.pop('admin_access', None)
        session.pop('last_seen', None)
        logout_user()
        flash('You have been logged out.', 'info')
    return redirect(url_for('admin_auth.admin_login'))
