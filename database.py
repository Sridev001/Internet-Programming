"""Database initialization and management."""
from extensions import db
from models import User, Flight, Booking
from werkzeug.security import generate_password_hash
import os
import logging
import sqlite3
from datetime import datetime, timedelta

def ensure_db_directory():
    """Ensure database directory exists and has correct permissions."""
    try:
        # Get the database path from current app config
        from flask import current_app
        db_path = current_app.config['DB_FILE']
        db_dir = os.path.dirname(db_path)
        
        # Create directory if it doesn't exist
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"Created database directory at {db_dir}")
        
        # Set directory permissions
        os.chmod(db_dir, 0o777)
        logging.info(f"Set permissions for directory: {db_dir}")
        
        # Create an empty database file if it doesn't exist
        if not os.path.exists(db_path):
            # Create the database file
            conn = sqlite3.connect(db_path)
            conn.close()
            logging.info(f"Created database file at {db_path}")
            
            # Set file permissions
            os.chmod(db_path, 0o666)
            logging.info(f"Set permissions for database file: {db_path}")
        
        return True
    except Exception as e:
        logging.error(f"Error ensuring database directory: {e}")
        return False

def init_users():
    """Initialize default users if they don't exist."""
    try:
        # Create admin user
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                is_admin=True,
                is_employee=True,
                department='Administration'
            )
            admin.set_password('admin123')  # Change in production
            db.session.add(admin)
            db.session.commit()
            logging.info('Created admin user')

        # Create employee user
        employee = User.query.filter_by(email='employee@skybooker.com').first()
        if not employee:
            employee = User(
                email='employee@skybooker.com',
                first_name='John',
                last_name='Smith',
                is_admin=False,
                is_employee=True,
                department='Customer Service'
            )
            employee.set_password('employee123')  # Change in production
            db.session.add(employee)
            db.session.commit()
            logging.info('Created employee user')

        # Create regular user
        user = User.query.filter_by(email='user@example.com').first()
        if not user:
            user = User(
                email='user@example.com',
                first_name='Regular',
                last_name='User',
                is_admin=False,
                is_employee=False
            )
            user.set_password('user123')  # Change in production
            db.session.add(user)
            db.session.commit()
            logging.info('Created regular user')

    except Exception as e:
        db.session.rollback()
        logging.error(f'Error creating users: {str(e)}')
        raise

def init_sample_flights():
    """Initialize sample flights if none exist."""
    try:
        # Only add sample flights if none exist
        if Flight.query.first() is None:
            # Get current date for reference
            now = datetime.now()
            
            # List of sample flights with realistic routes
            sample_flights = [
                # Today's flights
                {
                    'flight_number': 'SK101',
                    'origin': 'New York (JFK)',
                    'destination': 'London (LHR)',
                    'departure_time': now.replace(hour=8, minute=30),
                    'arrival_time': now.replace(hour=20, minute=45),
                    'price': 450.00,
                    'available_seats': 150,
                    'aircraft_type': 'Boeing 777'
                },
                {
                    'flight_number': 'SK102',
                    'origin': 'London (LHR)',
                    'destination': 'New York (JFK)',
                    'departure_time': now.replace(hour=11, minute=15),
                    'arrival_time': now.replace(hour=14, minute=30),
                    'price': 480.00,
                    'available_seats': 120,
                    'aircraft_type': 'Boeing 787'
                },
                
                # Tomorrow's flights
                {
                    'flight_number': 'SK201',
                    'origin': 'Los Angeles (LAX)',
                    'destination': 'Tokyo (NRT)',
                    'departure_time': (now + timedelta(days=1)).replace(hour=10, minute=0),
                    'arrival_time': (now + timedelta(days=2)).replace(hour=14, minute=30),
                    'price': 750.00,
                    'available_seats': 200,
                    'aircraft_type': 'Airbus A380'
                },
                {
                    'flight_number': 'SK202',
                    'origin': 'Paris (CDG)',
                    'destination': 'Dubai (DXB)',
                    'departure_time': (now + timedelta(days=1)).replace(hour=13, minute=45),
                    'arrival_time': (now + timedelta(days=1)).replace(hour=23, minute=15),
                    'price': 380.00,
                    'available_seats': 160,
                    'aircraft_type': 'Airbus A350'
                },
                
                # Day after tomorrow
                {
                    'flight_number': 'SK301',
                    'origin': 'Singapore (SIN)',
                    'destination': 'Sydney (SYD)',
                    'departure_time': (now + timedelta(days=2)).replace(hour=9, minute=20),
                    'arrival_time': (now + timedelta(days=2)).replace(hour=19, minute=45),
                    'price': 420.00,
                    'available_seats': 180,
                    'aircraft_type': 'Boeing 787'
                },
                {
                    'flight_number': 'SK302',
                    'origin': 'Dubai (DXB)',
                    'destination': 'London (LHR)',
                    'departure_time': (now + timedelta(days=2)).replace(hour=14, minute=30),
                    'arrival_time': (now + timedelta(days=2)).replace(hour=19, minute=0),
                    'price': 350.00,
                    'available_seats': 140,
                    'aircraft_type': 'Airbus A350'
                },
                
                # Next week flights
                {
                    'flight_number': 'SK401',
                    'origin': 'New York (JFK)',
                    'destination': 'Paris (CDG)',
                    'departure_time': (now + timedelta(days=7)).replace(hour=7, minute=0),
                    'arrival_time': (now + timedelta(days=7)).replace(hour=20, minute=30),
                    'price': 520.00,
                    'available_seats': 170,
                    'aircraft_type': 'Boeing 777'
                },
                {
                    'flight_number': 'SK402',
                    'origin': 'Hong Kong (HKG)',
                    'destination': 'Tokyo (NRT)',
                    'departure_time': (now + timedelta(days=7)).replace(hour=11, minute=45),
                    'arrival_time': (now + timedelta(days=7)).replace(hour=16, minute=30),
                    'price': 280.00,
                    'available_seats': 150,
                    'aircraft_type': 'Airbus A330'
                },
                
                # Two weeks ahead
                {
                    'flight_number': 'SK501',
                    'origin': 'London (LHR)',
                    'destination': 'Singapore (SIN)',
                    'departure_time': (now + timedelta(days=14)).replace(hour=10, minute=15),
                    'arrival_time': (now + timedelta(days=15)).replace(hour=6, minute=45),
                    'price': 680.00,
                    'available_seats': 190,
                    'aircraft_type': 'Airbus A380'
                },
                {
                    'flight_number': 'SK502',
                    'origin': 'Sydney (SYD)',
                    'destination': 'Los Angeles (LAX)',
                    'departure_time': (now + timedelta(days=14)).replace(hour=13, minute=30),
                    'arrival_time': (now + timedelta(days=14)).replace(hour=23, minute=45),
                    'price': 890.00,
                    'available_seats': 160,
                    'aircraft_type': 'Boeing 787'
                }
            ]
            
            # Add all flights to database
            for flight_data in sample_flights:
                flight = Flight(**flight_data)
                db.session.add(flight)
            
            db.session.commit()
            logging.info(f"Added {len(sample_flights)} sample flights")
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating sample flights: {str(e)}")
        raise

def init_db():
    """Initialize the database."""
    try:
        # Ensure database directory exists with correct permissions
        if not ensure_db_directory():
            raise Exception("Failed to ensure database directory")
        
        # Create all tables
        db.create_all()
        logging.info('Created database tables')
        
        # Initialize users
        init_users()
        
        # Initialize sample flights
        init_sample_flights()
        
        logging.info("Database initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise
