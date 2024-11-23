"""Admin forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

class AdminLoginForm(FlaskForm):
    """Admin login form."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(min=6, max=100)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=50)
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class AdminCancelBookingForm(FlaskForm):
    """Form for admin to cancel bookings without requiring a reference."""
    submit = SubmitField('Cancel Booking')
