"""Email utility functions for SkyBooker."""
from flask import render_template
from flask_mail import Message, Mail
from models import db
import logging

logger = logging.getLogger(__name__)
mail = Mail()

def init_mail(app):
    """Initialize the mail extension."""
    mail.init_app(app)

def send_booking_confirmation_email(booking):
    """Send booking confirmation email to passenger."""
    try:
        subject = f'SkyBooker - Booking Confirmation #{booking.booking_reference}'
        
        msg = Message(
            subject=subject,
            sender=('SkyBooker', 'noreply@skybooker.com'),
            recipients=[booking.user.email]
        )
        
        msg.html = render_template(
            'emails/booking_confirmation.html',
            booking=booking,
            user=booking.user,
            flight=booking.flight
        )
        
        mail.send(msg)
        logger.info(f'Sent booking confirmation email for {booking.booking_reference}')
        
    except Exception as e:
        logger.error(f'Error sending booking confirmation email: {str(e)}')
        raise

def send_booking_cancellation_email(booking, reason=''):
    """Send booking cancellation email to passenger."""
    try:
        subject = f'SkyBooker - Booking Cancellation #{booking.booking_reference}'
        
        msg = Message(
            subject=subject,
            sender=('SkyBooker', 'noreply@skybooker.com'),
            recipients=[booking.user.email]
        )
        
        msg.html = render_template(
            'emails/booking_cancellation.html',
            booking=booking,
            user=booking.user,
            flight=booking.flight,
            reason=reason
        )
        
        mail.send(msg)
        logger.info(f'Sent booking cancellation email for {booking.booking_reference}')
        
    except Exception as e:
        logger.error(f'Error sending booking cancellation email: {str(e)}')
        raise

def send_flight_update_email(booking):
    """Send flight update email to passenger."""
    try:
        subject = f'SkyBooker - Flight Update #{booking.flight.flight_number}'
        
        msg = Message(
            subject=subject,
            sender=('SkyBooker', 'noreply@skybooker.com'),
            recipients=[booking.user.email]
        )
        
        msg.html = render_template(
            'emails/flight_update.html',
            booking=booking,
            user=booking.user,
            flight=booking.flight
        )
        
        mail.send(msg)
        logger.info(f'Sent flight update email for booking {booking.booking_reference}')
        
    except Exception as e:
        logger.error(f'Error sending flight update email: {str(e)}')
        raise

def send_flight_cancellation_email(booking):
    """Send flight cancellation email to passenger."""
    try:
        subject = f'SkyBooker - Flight Cancellation #{booking.flight.flight_number}'
        
        msg = Message(
            subject=subject,
            sender=('SkyBooker', 'noreply@skybooker.com'),
            recipients=[booking.user.email]
        )
        
        msg.html = render_template(
            'emails/flight_cancellation.html',
            booking=booking,
            user=booking.user,
            flight=booking.flight
        )
        
        mail.send(msg)
        logger.info(f'Sent flight cancellation email for booking {booking.booking_reference}')
        
    except Exception as e:
        logger.error(f'Error sending flight cancellation email: {str(e)}')
        raise

def send_custom_email(email, subject, message):
    """Send custom email to passenger."""
    try:
        msg = Message(
            subject=subject,
            sender=('SkyBooker', 'noreply@skybooker.com'),
            recipients=[email]
        )
        
        msg.html = render_template(
            'emails/custom_message.html',
            message=message
        )
        
        mail.send(msg)
        logger.info(f'Sent custom email to {email}')
        
    except Exception as e:
        logger.error(f'Error sending custom email: {str(e)}')
        raise
