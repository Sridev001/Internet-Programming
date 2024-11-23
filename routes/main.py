from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Flight, Booking, PassengerDetail, Payment
from forms import FlightSearchForm, BookingForm, PassengerForm, CancelBookingForm, PaymentForm
from database import db
from datetime import datetime, timedelta
import random
import string
from datetime import date

main = Blueprint('main', __name__)

def generate_booking_reference():
    """Generate a random 6-character booking reference."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@main.route('/')
def index():
    search_form = FlightSearchForm()
    if search_form.validate_on_submit():
        flights = Flight.query.filter_by(
            origin=search_form.origin.data,
            destination=search_form.destination.data,
        ).filter(
            Flight.departure_time >= search_form.departure_date.data,
            Flight.departure_time < search_form.departure_date.data + timedelta(days=1),
            Flight.available_seats >= search_form.passengers.data
        ).all()
        
        if not flights:
            flash('No flights found for your search criteria.', 'info')
            return redirect(url_for('main.index'))
            
        return render_template('search_results.html', 
            flights=flights, 
            passengers=search_form.passengers.data,
            search_date=search_form.departure_date.data
        )
    
    # Get some featured flights for display
    featured_flights = Flight.query.filter(
        Flight.departure_time >= datetime.now(),
        Flight.available_seats > 0
    ).order_by(Flight.departure_time).limit(6).all()
    
    return render_template('index.html', 
        form=search_form, 
        featured_flights=featured_flights
    )

@main.route('/search', methods=['GET', 'POST'])
def search_flights():
    form = FlightSearchForm()
    if request.method == 'POST' and form.validate_on_submit():
        # Handle POST request with form validation
        flights = Flight.query.filter(
            Flight.origin.ilike(f"%{form.origin.data}%"),
            Flight.destination.ilike(f"%{form.destination.data}%"),
            Flight.departure_time >= form.departure_date.data,
            Flight.available_seats >= form.passengers.data
        ).all()
        
        search_params = {
            'origin': form.origin.data,
            'destination': form.destination.data,
            'departure_date': form.departure_date.data.strftime('%Y-%m-%d'),
            'passengers': form.passengers.data
        }
        return render_template('flights.html', flights=flights, search_params=search_params)
    elif request.method == 'GET':
        # Handle GET request with query parameters
        try:
            origin = request.args.get('origin', '')
            destination = request.args.get('destination', '')
            departure_date = datetime.strptime(request.args.get('departure_date', ''), '%Y-%m-%d').date()
            passengers = int(request.args.get('passengers', 1))
            
            flights = Flight.query.filter(
                Flight.origin.ilike(f"%{origin}%"),
                Flight.destination.ilike(f"%{destination}%"),
                Flight.departure_time >= departure_date,
                Flight.available_seats >= passengers
            ).all()
            
            search_params = {
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date.strftime('%Y-%m-%d'),
                'passengers': passengers
            }
            return render_template('flights.html', flights=flights, search_params=search_params)
        except (ValueError, TypeError) as e:
            flash('Invalid search parameters. Please try again.', 'error')
            return redirect(url_for('main.index'))
            
    return render_template('index.html', form=form)

@main.route('/book/<int:flight_id>', methods=['GET', 'POST'])
@login_required
def book_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    form = BookingForm()
    
    if form.validate_on_submit():
        if form.number_of_seats.data > flight.available_seats:
            flash('Not enough seats available.', 'error')
            return redirect(url_for('main.book_flight', flight_id=flight_id))
            
        booking = Booking(
            user_id=current_user.id,
            flight_id=flight_id,
            booking_reference=generate_booking_reference(),
            number_of_seats=form.number_of_seats.data,
            total_price=flight.price * form.number_of_seats.data,
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return redirect(url_for('main.add_passengers', booking_id=booking.id))
        
    return render_template('booking.html', flight=flight, form=form)

@main.route('/booking/<int:booking_id>/passengers', methods=['GET', 'POST'])
@login_required
def add_passengers(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # Create a list of passenger forms based on the number of seats
    passenger_forms = []
    for i in range(booking.number_of_seats):
        form = PassengerForm(prefix=f'passenger_{i}')
        passenger_forms.append(form)
    
    if request.method == 'POST':
        all_valid = True
        for form in passenger_forms:
            if not form.validate_on_submit():
                all_valid = False
                break
        
        if all_valid:
            # Save passenger details
            for i, form in enumerate(passenger_forms):
                passenger = PassengerDetail(
                    booking_id=booking.id,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    passport_number=form.passport_number.data,
                    date_of_birth=form.date_of_birth.data
                )
                db.session.add(passenger)
            
            # Update booking status and flight seats
            booking.status = 'pending_payment'
            db.session.commit()
            flash('Passenger details saved successfully!', 'success')
            return redirect(url_for('main.payment', booking_id=booking.id))
    
    return render_template(
        'add_passengers.html',
        booking=booking,
        forms=passenger_forms,
        flight=booking.flight
    )

@main.route('/booking/<int:booking_id>/payment', methods=['GET', 'POST'])
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    # Ensure booking has all passenger details
    if len(booking.passenger_details) != booking.number_of_seats:
        flash('Please complete passenger details first.', 'error')
        return redirect(url_for('main.add_passengers', booking_id=booking_id))
    
    form = PaymentForm()
    
    if form.validate_on_submit():
        try:
            # Process payment
            payment = Payment(
                booking_id=booking.id,
                amount=booking.total_price,
                card_number=form.card_number.data[-4:],  # Store only last 4 digits
                payment_status='completed'
            )
            
            # Update booking status
            booking.status = 'confirmed'
            flight = booking.flight
            flight.update_seats(booking.number_of_seats)
            
            db.session.add(payment)
            db.session.commit()
            
            # Send confirmation email (you can implement this later)
            # send_booking_confirmation_email(booking)
            
            flash('Payment successful! Your booking is confirmed.', 'success')
            return redirect(url_for('main.booking_confirmation', booking_id=booking.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Payment processing failed. Please try again.', 'error')
            return redirect(url_for('main.payment', booking_id=booking_id))
    
    return render_template(
        'payment.html',
        booking=booking,
        form=form,
        flight=booking.flight
    )

@main.route('/booking/<int:booking_id>/confirmation')
@login_required
def booking_confirmation(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
        
    if booking.status != 'confirmed':
        flash('Booking not confirmed yet.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('booking_confirmation.html', booking=booking)

@main.route('/booking/<int:booking_id>/view')
@login_required
def view_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('view_booking.html', booking=booking, today=date.today())

@main.route('/my-bookings')
@login_required
def my_bookings():
    # Create an empty form just for CSRF token
    form = CancelBookingForm()
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings, today=date.today(), form=form)

@main.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.my_bookings'))
    
    # Check if booking is already cancelled
    if booking.status == 'cancelled':
        flash('This booking is already cancelled.', 'error')
        return redirect(url_for('main.my_bookings'))
    
    # Check if the flight has already departed
    if booking.flight.departure_time.date() <= date.today():
        flash('Cannot cancel a booking for a flight that has already departed.', 'error')
        return redirect(url_for('main.my_bookings'))
    
    # Process cancellation
    booking.status = 'cancelled'
    booking.flight.available_seats += booking.number_of_seats
    db.session.commit()
    
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('main.my_bookings'))
