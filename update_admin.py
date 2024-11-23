from flask import Flask
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
import os

def create_app():
    app = Flask(__name__)
    
    # Ensure instance directory exists
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/skybooker.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app

def update_admin_password():
    app = create_app()
    with app.app_context():
        # Find admin user
        admin = User.query.filter_by(email='admin@example.com').first()
        
        if not admin:
            # Create admin if doesn't exist
            admin = User(
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                is_admin=True
            )
            db.session.add(admin)
        
        # Update password
        admin.password_hash = generate_password_hash('admin1')
        db.session.commit()
        print("Admin password updated successfully!")

if __name__ == '__main__':
    update_admin_password()
