"""Admin routes for the application."""
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for, session
from flask_login import login_required, current_user
from models import db, User, Flight, Booking, PassengerDetail
from forms.admin_forms import AdminCancelBookingForm
from functools import wraps
import logging
from sqlalchemy import func
from datetime import datetime, timedelta
import traceback

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to check if current user is an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.before_request
def check_session_timeout():
    """Check if admin session has timed out."""
    try:
        if current_user.is_authenticated and current_user.is_admin:
            if 'last_seen' not in session:
                session['last_seen'] = datetime.utcnow().isoformat()
            else:
                try:
                    last_seen = datetime.fromisoformat(session.get('last_seen'))
                    if datetime.utcnow() - last_seen > timedelta(minutes=30):
                        session.clear()
                        flash('Your session has expired. Please login again.', 'warning')
                        return redirect(url_for('auth.login'))
                    session['last_seen'] = datetime.utcnow().isoformat()
                except (ValueError, TypeError) as e:
                    logger.error(f"Session timestamp error: {str(e)}")
                    session['last_seen'] = datetime.utcnow().isoformat()
    except Exception as e:
        logger.error(f"Session check error: {str(e)}\n{traceback.format_exc()}")
        session.clear()
        return redirect(url_for('auth.login'))

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard showing key statistics."""
    try:
        # Get statistics
        total_users = User.query.count()
        total_flights = Flight.query.count()
        total_bookings = Booking.query.count()
        
        # Get recent bookings
        recent_bookings = Booking.query\
            .join(User)\
            .join(Flight)\
            .order_by(Booking.created_at.desc())\
            .limit(5)\
            .all()
        
        return render_template(
            'admin/dashboard.html',
            total_users=total_users,
            total_flights=total_flights,
            total_bookings=total_bookings,
            recent_bookings=recent_bookings
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}\n{traceback.format_exc()}")
        flash('An error occurred while loading the dashboard.', 'error')
        return render_template('errors/500.html'), 500

@admin_bp.route('/flights', methods=['GET', 'POST'])
@login_required
@admin_required
def flights():
    """Manage flights."""
    try:
        if request.method == 'GET':
            flights = Flight.query.order_by(Flight.departure_time.asc()).all()
            return render_template('admin/flights.html', flights=flights)
            
        elif request.method == 'POST':
            data = request.get_json()
            
            flight = Flight(
                flight_number=data['flight_number'],
                origin=data['origin'],
                destination=data['destination'],
                departure_time=datetime.fromisoformat(data['departure_time']),
                arrival_time=datetime.fromisoformat(data['arrival_time']),
                price=float(data['price']),
                total_seats=int(data['total_seats']),
                available_seats=int(data['total_seats'])
            )
            
            db.session.add(flight)
            db.session.commit()
            
            return jsonify({'message': 'Flight created successfully'}), 201
            
    except Exception as e:
        logger.error(f"Error managing flights: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users page."""
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin/users.html', users=users)
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        flash('Error loading users.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    """View all bookings."""
    try:
        form = AdminCancelBookingForm()  # Create form for CSRF token
        bookings = Booking.query\
            .join(User)\
            .join(Flight)\
            .order_by(Booking.created_at.desc())\
            .all()
        return render_template('admin/bookings.html', bookings=bookings, form=form)
    except Exception as e:
        logger.error(f"Error viewing bookings: {str(e)}\n{traceback.format_exc()}")
        flash('An error occurred while loading bookings.', 'error')
        return render_template('errors/500.html'), 500

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """View reports page."""
    try:
        # Get booking statistics
        total_bookings = Booking.query.count()
        total_revenue = db.session.query(func.sum(Booking.total_price)).scalar() or 0
        
        # Get popular routes
        popular_routes = db.session.query(
            Flight.origin,
            Flight.destination,
            func.count(Booking.id).label('booking_count')
        ).join(Booking).group_by(Flight.origin, Flight.destination)\
         .order_by(func.count(Booking.id).desc()).limit(5).all()
        
        # Get monthly booking stats
        monthly_stats = db.session.query(
            func.strftime('%Y-%m', Booking.created_at).label('month'),
            func.count(Booking.id).label('booking_count'),
            func.sum(Booking.total_price).label('revenue')
        ).group_by('month').order_by('month').all()
        
        return render_template('admin/reports.html',
                             total_bookings=total_bookings,
                             total_revenue=total_revenue,
                             popular_routes=popular_routes,
                             monthly_stats=monthly_stats)
    except Exception as e:
        logger.error(f"Error generating reports: {str(e)}")
        flash('Error generating reports.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/<int:user_id>/bookings')
@login_required
@admin_required
def user_bookings(user_id):
    """Get bookings for a specific user."""
    try:
        user = User.query.get_or_404(user_id)
        bookings = [{
            'reference': b.booking_reference,
            'flight': f"{b.flight.flight_number} ({b.flight.origin} → {b.flight.destination})",
            'seats': b.number_of_seats,
            'total': float(b.total_price),
            'status': b.status
        } for b in user.bookings]
        return jsonify({'success': True, 'bookings': bookings})
    except Exception as e:
        logger.error(f"Error fetching user bookings: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching bookings'}), 500

@admin_bp.route('/flights/<int:flight_id>/bookings')
@login_required
@admin_required
def flight_bookings(flight_id):
    """Get bookings for a specific flight."""
    try:
        flight = Flight.query.get_or_404(flight_id)
        bookings = [{
            'reference': b.booking_reference,
            'user': f"{b.user.first_name} {b.user.last_name} ({b.user.email})",
            'seats': b.number_of_seats,
            'total': float(b.total_price),
            'status': b.status
        } for b in flight.bookings]
        return jsonify({'success': True, 'bookings': bookings})
    except Exception as e:
        logger.error(f"Error fetching flight bookings: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching bookings'}), 500

@admin_bp.route('/flights/<int:flight_id>', methods=['GET'])
@login_required
@admin_required
def get_flight(flight_id):
    """Get flight details for editing."""
    try:
        flight = Flight.query.get_or_404(flight_id)
        return jsonify({
            'flight_id': flight.id,
            'flight_number': flight.flight_number,
            'origin': flight.origin,
            'destination': flight.destination,
            'departure_time': flight.departure_time.isoformat(),
            'arrival_time': flight.arrival_time.isoformat(),
            'price': float(flight.price),
            'total_seats': flight.total_seats
        })
    except Exception as e:
        logger.error(f"Error fetching flight details: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching flight details'}), 500

@admin_bp.route('/flights/<int:flight_id>', methods=['PUT'])
@login_required
@admin_required
def update_flight(flight_id):
    """Update flight details."""
    try:
        flight = Flight.query.get_or_404(flight_id)
        data = request.get_json()
        
        # Update flight details
        flight.flight_number = data['flight_number']
        flight.origin = data['origin']
        flight.destination = data['destination']
        flight.departure_time = datetime.fromisoformat(data['departure_time'])
        flight.arrival_time = datetime.fromisoformat(data['arrival_time'])
        flight.price = float(data['price'])
        flight.total_seats = int(data['total_seats'])
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Flight updated successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating flight: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating flight'}), 500
