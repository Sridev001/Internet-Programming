"""Employee routes for managing bookings and flights."""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, make_response
from flask_login import login_required, current_user
from models import Flight, Booking, User, db, BookingHistory, FlightHistory
from datetime import datetime
import logging
from functools import wraps
import csv
from io import StringIO

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')
logger = logging.getLogger(__name__)

def employee_required(f):
    """Decorator to require employee access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_employee:
            flash('Employee access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@employee_bp.route('/dashboard')
@login_required
@employee_required
def dashboard():
    """Employee dashboard showing overview of flights and bookings."""
    try:
        # Get today's flights
        today = datetime.now().date()
        todays_flights = Flight.query.filter(
            db.func.date(Flight.departure_time) == today
        ).order_by(Flight.departure_time.asc()).all()
        
        # Get recent bookings
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
        
        # Get statistics
        total_flights = Flight.query.count()
        total_bookings = Booking.query.count()
        available_flights = Flight.query.filter(Flight.available_seats > 0).count()
        
        return render_template('employee/dashboard.html',
                             todays_flights=todays_flights,
                             recent_bookings=recent_bookings,
                             total_flights=total_flights,
                             total_bookings=total_bookings,
                             available_flights=available_flights)
    except Exception as e:
        logger.error(f"Error accessing employee dashboard: {str(e)}")
        flash('Error loading dashboard.', 'error')
        return redirect(url_for('main.index'))

@employee_bp.route('/bookings')
@login_required
@employee_required
def bookings():
    """View and manage all bookings."""
    try:
        all_bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        return render_template('employee/bookings.html', bookings=all_bookings)
    except Exception as e:
        logger.error(f"Error accessing bookings: {str(e)}")
        flash('Error loading bookings.', 'error')
        return redirect(url_for('employee.dashboard'))

@employee_bp.route('/flights')
@login_required
@employee_required
def flights():
    """View all flights and their details."""
    try:
        all_flights = Flight.query.order_by(Flight.departure_time.asc()).all()
        return render_template('employee/flights.html', flights=all_flights)
    except Exception as e:
        logger.error(f"Error accessing flights: {str(e)}")
        flash('Error loading flights.', 'error')
        return redirect(url_for('employee.dashboard'))

@employee_bp.route('/booking/<string:reference>')
@login_required
@employee_required
def view_booking(reference):
    """View detailed booking information."""
    try:
        booking = Booking.query.filter_by(booking_reference=reference).first_or_404()
        return render_template('employee/view_booking.html', booking=booking, now=datetime.now())
    except Exception as e:
        logger.error(f"Error viewing booking {reference}: {str(e)}")
        flash('Error loading booking details.', 'error')
        return redirect(url_for('employee.bookings'))

@employee_bp.route('/flight/<int:flight_id>')
@login_required
@employee_required
def view_flight(flight_id):
    """View detailed flight information."""
    try:
        flight = Flight.query.get_or_404(flight_id)
        return render_template('employee/view_flight.html', flight=flight, now=datetime.now())
    except Exception as e:
        logger.error(f"Error viewing flight {flight_id}: {str(e)}")
        flash('Error loading flight details.', 'error')
        return redirect(url_for('employee.flights'))

@employee_bp.route('/search')
@login_required
@employee_required
def search():
    """Search for flights or bookings."""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'booking')
    
    try:
        if not query:
            return render_template('employee/search.html')
            
        if search_type == 'booking':
            # Search in bookings
            bookings = Booking.query.filter(
                (Booking.booking_reference.ilike(f'%{query}%')) |
                (db.exists().where(
                    (User.id == Booking.user_id) &
                    ((User.email.ilike(f'%{query}%')) |
                     (User.first_name.ilike(f'%{query}%')) |
                     (User.last_name.ilike(f'%{query}%')))
                ))
            ).all()
            return render_template('employee/search.html', bookings=bookings, query=query, search_type=search_type)
        else:
            # Search in flights
            flights = Flight.query.filter(
                (Flight.flight_number.ilike(f'%{query}%')) |
                (Flight.origin.ilike(f'%{query}%')) |
                (Flight.destination.ilike(f'%{query}%'))
            ).all()
            return render_template('employee/search.html', flights=flights, query=query, search_type=search_type)
            
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        flash('Error performing search.', 'error')
        return redirect(url_for('employee.dashboard'))

@employee_bp.route('/confirm_booking/<string:reference>', methods=['POST'])
@login_required
@employee_required
def confirm_booking(reference):
    """Confirm a pending booking."""
    try:
        booking = Booking.query.filter_by(booking_reference=reference).first_or_404()
        
        if booking.status != 'pending':
            flash('This booking cannot be confirmed.', 'error')
            return redirect(url_for('employee.view_booking', reference=reference))
        
        booking.status = 'confirmed'
        booking.updated_at = datetime.now()
        
        # Add to booking history
        history = BookingHistory(
            booking_id=booking.id,
            user_id=current_user.id,
            action='confirm',
            description='Booking confirmed by employee',
            timestamp=datetime.now()
        )
        db.session.add(history)
        
        # Send confirmation email
        send_booking_confirmation_email(booking)
        
        db.session.commit()
        flash('Booking confirmed successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming booking {reference}: {str(e)}")
        flash('Error confirming booking.', 'error')
    
    return redirect(url_for('employee.view_booking', reference=reference))

@employee_bp.route('/cancel_booking/<string:reference>', methods=['POST'])
@login_required
@employee_required
def cancel_booking(reference):
    """Cancel a booking."""
    try:
        booking = Booking.query.filter_by(booking_reference=reference).first_or_404()
        
        if booking.status == 'cancelled':
            flash('This booking is already cancelled.', 'error')
            return redirect(url_for('employee.view_booking', reference=reference))
        
        reason = request.form.get('reason', '')
        notify = request.form.get('notify', 'off') == 'on'
        
        booking.status = 'cancelled'
        booking.updated_at = datetime.now()
        
        # Update flight available seats
        booking.flight.available_seats += booking.number_of_seats
        
        # Add to booking history
        history = BookingHistory(
            booking_id=booking.id,
            user_id=current_user.id,
            action='cancel',
            description=f'Booking cancelled by employee. Reason: {reason}',
            timestamp=datetime.now()
        )
        db.session.add(history)
        
        # Send cancellation email if requested
        if notify:
            send_booking_cancellation_email(booking, reason)
        
        db.session.commit()
        flash('Booking cancelled successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling booking {reference}: {str(e)}")
        flash('Error cancelling booking.', 'error')
    
    return redirect(url_for('employee.view_booking', reference=reference))

@employee_bp.route('/edit_flight/<int:flight_id>', methods=['POST'])
@login_required
@employee_required
def edit_flight(flight_id):
    """Edit flight details."""
    try:
        flight = Flight.query.get_or_404(flight_id)
        
        # Update flight details
        flight.price = float(request.form['price'])
        flight.departure_time = datetime.strptime(request.form['departure_time'], '%Y-%m-%dT%H:%M')
        flight.arrival_time = datetime.strptime(request.form['arrival_time'], '%Y-%m-%dT%H:%M')
        flight.updated_at = datetime.now()
        
        # Add to flight history
        history = FlightHistory(
            flight_id=flight.id,
            user_id=current_user.id,
            action='edit',
            description='Flight details updated by employee',
            timestamp=datetime.now()
        )
        db.session.add(history)
        
        # Notify affected passengers if departure time changed
        if flight.departure_time != flight.departure_time:
            for booking in flight.bookings:
                if booking.status == 'confirmed':
                    send_flight_update_email(booking)
        
        db.session.commit()
        flash('Flight details updated successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating flight {flight_id}: {str(e)}")
        flash('Error updating flight details.', 'error')
    
    return redirect(url_for('employee.view_flight', flight_id=flight_id))

@employee_bp.route('/cancel_flight/<int:flight_id>', methods=['POST'])
@login_required
@employee_required
def cancel_flight(flight_id):
    """Cancel a flight and all its bookings."""
    try:
        flight = Flight.query.get_or_404(flight_id)
        
        # Cancel all confirmed bookings
        for booking in flight.bookings:
            if booking.status == 'confirmed':
                booking.status = 'cancelled'
                booking.updated_at = datetime.now()
                
                # Add to booking history
                history = BookingHistory(
                    booking_id=booking.id,
                    user_id=current_user.id,
                    action='cancel',
                    description='Booking cancelled due to flight cancellation',
                    timestamp=datetime.now()
                )
                db.session.add(history)
                
                # Notify passenger
                send_flight_cancellation_email(booking)
        
        # Add to flight history
        history = FlightHistory(
            flight_id=flight.id,
            user_id=current_user.id,
            action='cancel',
            description='Flight cancelled by employee',
            timestamp=datetime.now()
        )
        db.session.add(history)
        
        # Mark flight as cancelled
        flight.status = 'cancelled'
        flight.updated_at = datetime.now()
        
        db.session.commit()
        flash('Flight and all associated bookings cancelled successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling flight {flight_id}: {str(e)}")
        flash('Error cancelling flight.', 'error')
    
    return redirect(url_for('employee.view_flight', flight_id=flight_id))

@employee_bp.route('/send_email/<string:reference>', methods=['POST'])
@login_required
@employee_required
def send_email(reference):
    """Send custom email to passenger."""
    try:
        booking = Booking.query.filter_by(booking_reference=reference).first_or_404()
        
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        if not subject or not message:
            flash('Subject and message are required.', 'error')
            return redirect(url_for('employee.view_booking', reference=reference))
        
        # Send email
        send_custom_email(booking.user.email, subject, message)
        
        # Add to booking history
        history = BookingHistory(
            booking_id=booking.id,
            user_id=current_user.id,
            action='email',
            description=f'Custom email sent to passenger. Subject: {subject}',
            timestamp=datetime.now()
        )
        db.session.add(history)
        db.session.commit()
        
        flash('Email sent successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending email for booking {reference}: {str(e)}")
        flash('Error sending email.', 'error')
    
    return redirect(url_for('employee.view_booking', reference=reference))

@employee_bp.route('/export_passenger_list/<int:flight_id>')
@login_required
@employee_required
def export_passenger_list(flight_id):
    """Export passenger list for a flight."""
    try:
        flight = Flight.query.get_or_404(flight_id)
        
        # Generate CSV content
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Booking Reference', 'Passenger Name', 'Email', 'Seats', 'Status'])
        
        for booking in flight.bookings:
            writer.writerow([
                booking.booking_reference,
                f"{booking.user.first_name} {booking.user.last_name}",
                booking.user.email,
                booking.number_of_seats,
                booking.status
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=passengers_flight_{flight.flight_number}.csv'
        
        # Add to flight history
        history = FlightHistory(
            flight_id=flight.id,
            user_id=current_user.id,
            action='export',
            description='Passenger list exported',
            timestamp=datetime.now()
        )
        db.session.add(history)
        db.session.commit()
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting passenger list for flight {flight_id}: {str(e)}")
        flash('Error exporting passenger list.', 'error')
        return redirect(url_for('employee.view_flight', flight_id=flight_id))

@employee_bp.route('/download_ticket/<string:reference>')
@login_required
@employee_required
def download_ticket(reference):
    """Download booking ticket."""
    try:
        booking = Booking.query.filter_by(booking_reference=reference).first_or_404()
        
        # Generate PDF ticket
        pdf = generate_ticket_pdf(booking)
        
        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=ticket_{booking.booking_reference}.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading ticket for booking {reference}: {str(e)}")
        flash('Error downloading ticket.', 'error')
        return redirect(url_for('employee.view_booking', reference=reference))
