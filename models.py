"""Database models for the application."""
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for authentication."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    is_employee = db.Column(db.Boolean, default=False)
    department = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches."""
        return check_password_hash(self.password_hash, password)

class Flight(db.Model):
    """Flight model for managing flight information."""
    
    __tablename__ = 'flights'
    
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), unique=True, nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_seats = db.Column(db.Integer, nullable=False, default=200)
    available_seats = db.Column(db.Integer, nullable=False)
    aircraft_type = db.Column(db.String(50), nullable=False, default='Boeing 737')
    bookings = db.relationship('Booking', backref='flight', lazy=True)
    
    def update_seats(self, booked_seats):
        """Update available seats after a booking."""
        if self.available_seats >= booked_seats:
            self.available_seats -= booked_seats
            db.session.commit()
            return True
        return False

class Booking(db.Model):
    """Booking model for managing flight bookings."""
    
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    booking_reference = db.Column(db.String(10), unique=True, nullable=False)
    number_of_seats = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    passenger_details = db.relationship('PassengerDetail', backref='booking', lazy=True)

class PassengerDetail(db.Model):
    """Passenger details model for storing passenger information."""
    
    __tablename__ = 'passenger_details'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    passport_number = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    """Payment model for handling payment information."""
    
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    card_number = db.Column(db.String(4), nullable=False)  # Last 4 digits only
    payment_status = db.Column(db.String(20), nullable=False, default='pending')
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    booking = db.relationship('Booking', backref=db.backref('payment', uselist=False))

class BookingHistory(db.Model):
    """History of booking actions."""
    __tablename__ = 'booking_history'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    booking = db.relationship('Booking', backref=db.backref('history', lazy=True))
    user = db.relationship('User', backref=db.backref('booking_actions', lazy=True))

class FlightHistory(db.Model):
    """History of flight actions."""
    __tablename__ = 'flight_history'
    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    flight = db.relationship('Flight', backref=db.backref('history', lazy=True))
    user = db.relationship('User', backref=db.backref('flight_actions', lazy=True))
