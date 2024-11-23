"""PDF generation utilities for SkyBooker."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
import qrcode
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_ticket_pdf(booking):
    """Generate a PDF ticket for a booking."""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph('SkyBooker Flight Ticket', title_style))
        
        # Booking Information
        booking_info = [
            ['Booking Reference:', booking.booking_reference],
            ['Status:', booking.status.upper()],
            ['Booking Date:', booking.created_at.strftime('%Y-%m-%d %H:%M')],
            ['Number of Seats:', str(booking.number_of_seats)],
            ['Total Price:', f'${booking.total_price:.2f}'],
        ]
        
        # Passenger Information
        passenger_info = [
            ['Passenger Name:', f'{booking.user.first_name} {booking.user.last_name}'],
            ['Email:', booking.user.email],
            ['Phone:', booking.user.phone or 'N/A'],
        ]
        
        # Flight Information
        flight_info = [
            ['Flight Number:', booking.flight.flight_number],
            ['From:', booking.flight.origin],
            ['To:', booking.flight.destination],
            ['Departure:', booking.flight.departure_time.strftime('%Y-%m-%d %H:%M')],
            ['Arrival:', booking.flight.arrival_time.strftime('%Y-%m-%d %H:%M')],
        ]
        
        # Create tables
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Add section headers and tables
        section_style = styles['Heading2']
        
        story.append(Paragraph('Booking Information', section_style))
        story.append(Spacer(1, 12))
        story.append(Table(booking_info, colWidths=[2*inch, 4*inch], style=table_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph('Passenger Information', section_style))
        story.append(Spacer(1, 12))
        story.append(Table(passenger_info, colWidths=[2*inch, 4*inch], style=table_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph('Flight Information', section_style))
        story.append(Spacer(1, 12))
        story.append(Table(flight_info, colWidths=[2*inch, 4*inch], style=table_style))
        story.append(Spacer(1, 20))
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_data = f"Booking: {booking.booking_reference}\nFlight: {booking.flight.flight_number}\nPassenger: {booking.user.first_name} {booking.user.last_name}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to buffer
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer)
        qr_buffer.seek(0)
        
        # Add QR code to PDF
        story.append(Paragraph('Boarding QR Code', section_style))
        story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f'Error generating ticket PDF: {str(e)}')
        raise
