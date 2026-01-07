"""
Email Service - Send order confirmations and notifications
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import Dict, Any, Optional
import os
from config import DB_NAME


class EmailService:
    """Handle email notifications for orders and bookings"""

    def __init__(self):
        # Email configuration from environment
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "concierge@raava.com")
        self.from_name = "Raava AI Concierge"

        # Fallback to console logging if email not configured
        self.email_enabled = bool(self.smtp_user and self.smtp_password)

    def send_order_confirmation(self, order: Dict[str, Any]) -> bool:
        """Send order confirmation email to customer"""
        try:
            customer_email = order.get("customer", {}).get("email")

            if not customer_email:
                print("❌ No customer email found")
                return False

            # Generate email content based on order type
            subject, html_body = self._generate_order_email(order)

            if self.email_enabled:
                return self._send_email(customer_email, subject, html_body)
            else:
                # Console fallback for development
                print("\n" + "=" * 70)
                print("📧 EMAIL NOTIFICATION (Development Mode)")
                print("=" * 70)
                print(f"To: {customer_email}")
                print(f"Subject: {subject}")
                print("\n" + html_body)
                print("=" * 70 + "\n")
                return True

        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False

    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Attach HTML body
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"✅ Email sent to {to_email}")
            return True

        except Exception as e:
            print(f"❌ SMTP error: {e}")
            return False

    def _generate_order_email(self, order: Dict[str, Any]) -> tuple:
        """Generate email subject and body based on order type"""
        order_type = order.get("order_type", "purchase")
        order_id = order.get("order_id", "")
        vehicle = order.get("vehicle", {})
        customer = order.get("customer", {})

        vehicle_title = f"{vehicle.get('make', '')} {vehicle.get('model', '')} ({vehicle.get('year', '')})"

        if order_type == "purchase":
            subject = f"✅ Order Confirmed - {vehicle_title} | {order_id}"
            body = self._generate_purchase_email(order, vehicle_title)

        elif order_type == "rental":
            subject = f"✅ Rental Booking Confirmed - {vehicle_title} | {order_id}"
            body = self._generate_rental_email(order, vehicle_title)

        elif order_type == "booking":
            booking_type = order.get("booking", {}).get("type", "viewing")
            action = "Test Drive" if booking_type == "test_drive" else "Viewing"
            subject = f"✅ {action} Confirmed - {vehicle_title} | {order_id}"
            body = self._generate_booking_email(order, vehicle_title)

        else:
            subject = f"✅ Order Confirmed - {order_id}"
            body = self._generate_generic_email(order)

        return subject, body

    def _generate_purchase_email(self, order: Dict, vehicle_title: str) -> str:
        """Generate purchase order confirmation email"""
        order_id = order["order_id"]
        vehicle = order["vehicle"]
        customer = order["customer"]
        finance = order.get("finance", {})
        created_at = order.get("created_at", datetime.utcnow())

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: white; padding: 30px; text-align: center; }}
        .logo {{ font-size: 32px; font-weight: bold; letter-spacing: 2px; }}
        .content {{ background: white; padding: 30px; border: 1px solid #eee; }}
        .order-id {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; }}
        .vehicle-details {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .finance-box {{ background: #e8f5e9; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .next-steps {{ background: #fff3cd; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        h2 {{ color: #1a1a1a; }}
        .highlight {{ color: #28a745; font-weight: bold; }}
        .price {{ font-size: 24px; color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">RAAVA</div>
            <p>Luxury Automotive Platform</p>
        </div>
        
        <div class="content">
            <h2>✅ Purchase Order Confirmed</h2>
            
            <div class="order-id">
                <strong>Order ID:</strong> {order_id}<br>
                <strong>Date:</strong> {created_at.strftime('%d %B %Y, %H:%M')}
            </div>
            
            <div class="vehicle-details">
                <h3>🚗 Vehicle Details</h3>
                <p><strong>Vehicle:</strong> {vehicle_title}</p>
                <p><strong>Price:</strong> <span class="price">£{vehicle.get('price', 0):,}</span></p>
                <p><strong>Mileage:</strong> {vehicle.get('mileage', 0):,} miles</p>
                <p><strong>Fuel Type:</strong> {vehicle.get('fuel_type', 'Petrol')}</p>
                <p><strong>Location:</strong> {vehicle.get('source', 'Raava Exclusive')}</p>
            </div>"""

        if finance:
            html += f"""
            <div class="finance-box">
                <h3>💰 Finance Details</h3>
                <p><strong>Finance Type:</strong> {finance.get('type', 'N/A')}</p>
                <p><strong>Provider:</strong> {finance.get('provider', 'N/A')}</p>
                <p><strong>Monthly Payment:</strong> <span class="highlight">£{finance.get('monthly_payment', 0):,.2f}</span></p>
                <p><strong>Term:</strong> {finance.get('term_months', 0)} months</p>
                <p><strong>Deposit:</strong> £{finance.get('deposit_amount', 0):,.2f}</p>
                <p><strong>APR:</strong> {finance.get('apr', 0)}%</p>
                <p><strong>Total Amount:</strong> £{finance.get('total_cost', 0):,.2f}</p>
            </div>"""

        html += f"""
            <div class="next-steps">
                <h3>📋 Next Steps</h3>
                <ol>
                    <li>You'll receive a detailed confirmation within <strong>15 minutes</strong></li>
                    <li>Finance application will be processed within <strong>24 hours</strong></li>
                    <li>Our team will contact you to arrange delivery</li>
                    <li>Vehicle preparation: <strong>3-5 working days</strong></li>
                </ol>
                <p><strong>Payment:</strong> Secure payment link will be sent via email</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px;">
                <h3>👤 Customer Details</h3>
                <p><strong>Name:</strong> {customer.get('name', '')}</p>
                <p><strong>Email:</strong> {customer.get('email', '')}</p>
                <p><strong>Phone:</strong> {customer.get('phone', '')}</p>
                <p><strong>Delivery Address:</strong> {customer.get('address', 'To be confirmed')}</p>
            </div>
            
            <p style="margin-top: 30px;">Thank you for choosing Raava. Your luxury automotive experience begins now! 🚗✨</p>
            
            <p style="color: #666; font-size: 14px; margin-top: 20px;">
                If you have any questions, please reply to this email or contact us at <a href="mailto:concierge@raava.com">concierge@raava.com</a>
            </p>
        </div>
        
        <div class="footer">
            <p>© 2026 Raava Luxury Automotive Platform. All rights reserved.</p>
            <p>This is an automated message from Raava AI Concierge</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_rental_email(self, order: Dict, vehicle_title: str) -> str:
        """Generate rental booking confirmation email"""
        order_id = order["order_id"]
        vehicle = order["vehicle"]
        customer = order["customer"]
        rental = order.get("rental", {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: white; padding: 30px; text-align: center; }}
        .content {{ background: white; padding: 30px; border: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 32px; font-weight: bold; letter-spacing: 2px;">RAAVA</div>
            <p>Luxury Automotive Platform</p>
        </div>
        
        <div class="content">
            <h2>✅ Rental Booking Confirmed</h2>
            
            <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                <strong>Booking ID:</strong> {order_id}
            </div>
            
            <h3>🚗 Vehicle: {vehicle_title}</h3>
            <p><strong>Daily Rate:</strong> £{rental.get('daily_rate', 0):,}</p>
            
            <div style="background: #e3f2fd; padding: 20px; margin: 20px 0; border-radius: 8px;">
                <h3>📅 Rental Period</h3>
                <p><strong>Start Date:</strong> {rental.get('start_date', datetime.utcnow()).strftime('%d %B %Y')}</p>
                <p><strong>End Date:</strong> {rental.get('end_date', datetime.utcnow()).strftime('%d %B %Y')}</p>
                <p><strong>Duration:</strong> {rental.get('duration_days', 0)} days</p>
                <p><strong>Total Cost:</strong> <span style="color: #007bff; font-size: 20px; font-weight: bold;">£{rental.get('total_rental_cost', 0):,}</span></p>
            </div>
            
            <p><strong>Mileage Limit:</strong> {rental.get('mileage_limit', 0)} miles</p>
            <p><strong>Insurance:</strong> {'Included ✅' if rental.get('insurance_included') else 'Not Included'}</p>
            <p><strong>Deposit Required:</strong> £{rental.get('deposit_required', 0):,}</p>
            
            <p style="margin-top: 30px;">Enjoy your luxury driving experience! 🚗✨</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_booking_email(self, order: Dict, vehicle_title: str) -> str:
        """Generate viewing/test drive confirmation email"""
        order_id = order["order_id"]
        customer = order["customer"]
        booking = order.get("booking", {})
        booking_type = (
            "Test Drive" if booking.get("type") == "test_drive" else "Viewing"
        )

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: white; padding: 30px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 32px; font-weight: bold; letter-spacing: 2px;">RAAVA</div>
        </div>
        
        <div style="background: white; padding: 30px; border: 1px solid #eee;">
            <h2>✅ {booking_type} Confirmed</h2>
            
            <p><strong>Booking ID:</strong> {order_id}</p>
            <p><strong>Vehicle:</strong> {vehicle_title}</p>
            
            <div style="background: #fff3cd; padding: 20px; margin: 20px 0; border-radius: 8px;">
                <h3>📅 Appointment Details</h3>
                <p><strong>Date:</strong> {booking.get('preferred_date', datetime.utcnow()).strftime('%d %B %Y')}</p>
                <p><strong>Time:</strong> {booking.get('preferred_time', 'TBC')}</p>
                <p><strong>Duration:</strong> {booking.get('duration_minutes', 60)} minutes</p>
                <p><strong>Location:</strong> {booking.get('location', 'Dealer Location')}</p>
            </div>
            
            <h3>What to Bring:</h3>
            <ul>
                <li>Valid UK driving licence (for test drives)</li>
                <li>Proof of address</li>
                <li>Photo ID</li>
            </ul>
            
            <p>We look forward to welcoming you! If you need to reschedule, please contact us 24 hours in advance.</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_generic_email(self, order: Dict) -> str:
        """Generate generic order confirmation"""
        return f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>Order Confirmed</h2>
    <p>Order ID: {order.get('order_id', '')}</p>
    <p>Thank you for your order. Our team will contact you shortly.</p>
</body>
</html>
"""


# Singleton instance
email_service = EmailService()
