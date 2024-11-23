"""Flight-related forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Regexp
from datetime import date

class AgeValidator:
    def __init__(self, min_age):
        self.min_age = min_age

    def __call__(self, form, field):
        message = f'You must be at least {self.min_age} years old to register.'
        date_of_birth = field.data
        age = date.today().year - date_of_birth.year - ((date.today().month, date.today().day) < (date_of_birth.month, date_of_birth.day))
        if age < self.min_age:
            raise ValidationError(message)

class FlightSearchForm(FlaskForm):
    origin = StringField('From', validators=[DataRequired()])
    destination = StringField('To', validators=[DataRequired()])
    departure_date = DateField('Departure Date', validators=[DataRequired()])
    passengers = IntegerField('Number of Passengers', 
        validators=[
            DataRequired(),
            NumberRange(min=1, max=10, message='Please select between 1 and 10 passengers')
        ],
        default=1
    )
    submit = SubmitField('Search Flights')

    def validate_departure_date(self, field):
        if field.data < date.today():
            raise ValidationError('Departure date cannot be in the past')

class BookingForm(FlaskForm):
    number_of_seats = IntegerField(
        'Number of Seats',
        validators=[
            DataRequired(),
            NumberRange(min=1, max=10, message='Please select between 1 and 10 seats')
        ],
        default=1
    )
    submit = SubmitField('Proceed to Passenger Details')

class PassengerForm(FlaskForm):
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(min=2, max=50)
    ])
    passport_number = StringField('Passport Number', validators=[
        DataRequired(),
        Length(min=6, max=20),
        Regexp(r'^[A-Z0-9]+$', message='Passport number must contain only uppercase letters and numbers')
    ])
    date_of_birth = DateField('Date of Birth', validators=[
        DataRequired(),
        AgeValidator(min_age=2)
    ])

class PaymentForm(FlaskForm):
    card_number = StringField('Card Number', validators=[
        DataRequired(),
        Length(min=16, max=16),
        Regexp(r'^\d{16}$', message='Card number must be 16 digits')
    ])
    expiry_month = SelectField('Expiry Month', 
        choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(1, 13)],
        validators=[DataRequired()]
    )
    expiry_year = SelectField('Expiry Year',
        choices=[(str(i), str(i)) for i in range(date.today().year, date.today().year + 11)],
        validators=[DataRequired()]
    )
    cvv = StringField('CVV', validators=[
        DataRequired(),
        Length(min=3, max=4),
        Regexp(r'^\d{3,4}$', message='CVV must be 3 or 4 digits')
    ])
    name_on_card = StringField('Name on Card', validators=[
        DataRequired(),
        Length(min=2, max=100),
        Regexp(r'^[A-Za-z\s]+$', message='Name can only contain letters and spaces')
    ])
    submit = SubmitField('Pay Now')

class CancelBookingForm(FlaskForm):
    booking_reference = StringField('Booking Reference', validators=[DataRequired()])
    submit = SubmitField('Cancel Booking')
