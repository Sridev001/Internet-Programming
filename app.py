"""Main application module."""
from flask import Flask, render_template, redirect, url_for, jsonify, request, flash, send_file
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from extensions import db
from models import User, Flight, Booking, PassengerDetail
from routes.main import main as main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.admin_auth import admin_auth_bp
from config import Config
import logging
import os
from werkzeug.middleware.proxy_fix import ProxyFix
import datetime
from io import BytesIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize extensions
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def ensure_directories_exist(app):
    """Ensure all required directories exist."""
    try:
        # Create instance directory if it doesn't exist
        if not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path, exist_ok=True)
            logger.info(f"Created instance directory at {app.instance_path}")
        
        # Create session directory if it doesn't exist
        session_dir = os.path.join(app.instance_path, 'flask_session')
        if not os.path.exists(session_dir):
            os.makedirs(session_dir, exist_ok=True)
            logger.info(f"Created session directory at {session_dir}")
        
        # Ensure the directories are writable
        os.chmod(app.instance_path, 0o777)
        os.chmod(session_dir, 0o777)
        
        logger.info("Successfully created and configured directories")
        return True
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)  # Enable CORS for all domains during development
    app.config.from_object(config_class)
    
    # Ensure directories exist
    if not ensure_directories_exist(app):
        logger.error("Failed to create required directories")
        raise RuntimeError("Failed to create required directories")
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_auth_bp)
    
    # Initialize database
    with app.app_context():
        try:
            from database import init_db
            init_db()
            logger.info("Database initialized successfully")
            
            # Create admin user if not exists
            admin = User.query.filter_by(email='admin@example.com').first()
            if not admin:
                admin = User(
                    email='admin@example.com',
                    first_name='Admin',
                    last_name='User',
                    is_admin=True
                )
                admin.set_password('admin1')
                db.session.add(admin)
            else:
                admin.set_password('admin1')
            db.session.commit()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise RuntimeError("Failed to initialize database")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)
