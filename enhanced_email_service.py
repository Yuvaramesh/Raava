"""
Enhanced Email Service - With proper Gmail configuration
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from datetime import datetime
import os


class EmailConfiguration:
    """Email configuration with Gmail support"""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = True

        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "Raava AI Concierge")
        self.company_name = os.getenv("COMPANY_NAME", "Raava")
        self.support_email = os.getenv("SUPPORT_EMAIL", "support@raava.com")

        self.email_enabled = bool(self.smtp_user and self.smtp_password)

        if self.email_enabled:
            print(f"✅ Email service configured")
            print(f"   📧 SMTP: {self.smtp_host}:{self.smtp_port}")
            print(f"   📤 From: {self.from_email}")
        else:
            print("⚠️ Email service not configured (will use console mode)")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "smtp_host": self.smtp_host,
            "from_email": self.from_email,
            "email_enabled": self.email_enabled,
        }


class EnhancedEmailService:
    """Email service with templates and Gmail support"""

    def __init__(self):
        self.config = EmailConfiguration()

    def send_order_confirmation(self, order: Dict[str, Any]) -> bool:
        """Send order confirmation email"""
        try:
            customer_email = order.get("customer", {}).get("email")
            if not customer_email:
                print("⚠️ No customer email provided")
                return False

            vehicle = order.get("vehicle", {})
            customer = order.get("customer", {})
            finance = order.get("finance", {})

            subject = f"✅ Order Confirmed - {order.get('order_id')}"

            # Build email body
            html_body = self._build_order_confirmation_html(
                order, vehicle, customer, finance
            )

            # Send email
            result = self._send_email(customer_email, subject, html_body)

            if result:
                print(f"✅ Order confirmation sent to {customer_email}")
            else:
                print(f"⚠️ Failed to send email to {customer_email}")

            return result

        except Exception as e:
            print(f"❌ Email error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _build_order_confirmation_html(
        self,
        order: Dict[str, Any],
        vehicle: Dict[str, Any],
        customer: Dict[str, Any],
        finance: Dict[str, Any],
    ) -> str:
        """Build HTML email body"""

        # Finance details section (if applicable)
        finance_section = ""
        if finance:
            finance_section = f"""
        <div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-left: 4px solid #007bff;">
            <h3 style="margin-top: 0; color: #007bff;">💰 Finance Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0;"><strong>Type:</strong></td>
                    <td style="padding: 8px 0;">{finance.get('type', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Provider:</strong></td>
                    <td style="padding: 8px 0;">{finance.get('provider', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Monthly Payment:</strong></td>
                    <td style="padding: 8px 0; font-size: 18px; color: #28a745;"><strong>£{finance.get('monthly_payment', 0):,.2f}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Term:</strong></td>
                    <td style="padding: 8px 0;">{finance.get('term_months', 0)} months</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Deposit:</strong></td>
                    <td style="padding: 8px 0;">£{finance.get('deposit_amount', 0):,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>APR:</strong></td>
                    <td style="padding: 8px 0;">{finance.get('apr', 0)}%</td>
                </tr>
            </table>
        </div>
        """

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a1a1a 0%, #333 100%); color: white; padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; font-size: 32px; font-weight: 700; letter-spacing: 2px;">{self.config.company_name}</h1>
                            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9; letter-spacing: 1px;">LUXURY AUTOMOTIVE PLATFORM</p>
                        </td>
                    </tr>
                    
                    <!-- Success Badge -->
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <div style="display: inline-block; background: #28a745; color: white; padding: 12px 30px; border-radius: 25px; font-size: 18px; font-weight: 600;">
                                ✅ Order Confirmed
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Order ID Box -->
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                                <table width="100%">
                                    <tr>
                                        <td style="padding: 5px 0;"><strong>Order ID:</strong></td>
                                        <td style="padding: 5px 0; text-align: right; font-family: monospace; color: #007bff;">{order.get('order_id')}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px 0;"><strong>Date:</strong></td>
                                        <td style="padding: 5px 0; text-align: right;">{order.get('created_at', datetime.utcnow()).strftime('%d %B %Y, %H:%M')}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px 0;"><strong>Status:</strong></td>
                                        <td style="padding: 5px 0; text-align: right;"><span style="background: #ffc107; color: #000; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">PENDING</span></td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Vehicle Details -->
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">🚗 Vehicle Details</h3>
                            <table width="100%" style="margin-bottom: 10px;">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Vehicle:</td>
                                    <td style="padding: 8px 0; text-align: right; font-weight: 600; font-size: 16px;">{vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('year')})</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Price:</td>
                                    <td style="padding: 8px 0; text-align: right; font-size: 20px; color: #28a745; font-weight: 700;">£{vehicle.get('price', 0):,}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Mileage:</td>
                                    <td style="padding: 8px 0; text-align: right;">{vehicle.get('mileage', 0):,} miles</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Fuel Type:</td>
                                    <td style="padding: 8px 0; text-align: right;">{vehicle.get('fuel_type', 'Petrol')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Body Type:</td>
                                    <td style="padding: 8px 0; text-align: right;">{vehicle.get('body_type', 'Coupe')}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Finance Details (if applicable) -->
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            {finance_section}
                        </td>
                    </tr>
                    
                    <!-- Customer Details -->
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">👤 Customer Information</h3>
                            <table width="100%">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Name:</td>
                                    <td style="padding: 8px 0; text-align: right; font-weight: 600;">{customer.get('name')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Email:</td>
                                    <td style="padding: 8px 0; text-align: right;">{customer.get('email')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Phone:</td>
                                    <td style="padding: 8px 0; text-align: right;">{customer.get('phone')}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Next Steps -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff;">
                                <h3 style="margin: 0 0 15px 0; color: #007bff;">📋 Next Steps</h3>
                                <ol style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                    <li>You'll receive a confirmation email within 15 minutes</li>
                                    <li>{'Finance application will be processed within 24 hours' if finance else 'Payment instructions will be sent shortly'}</li>
                                    <li>Our team will contact you to arrange delivery</li>
                                    <li>Vehicle preparation: 3-5 working days</li>
                                </ol>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center;">
                            <a href="mailto:{self.config.support_email}" style="display: inline-block; background: #007bff; color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-weight: 600; font-size: 16px;">Contact Support</a>
                        </td>
                    </tr>
                    
                    <!-- Thank You Message -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center; color: #666; line-height: 1.6;">
                            <p style="margin: 0; font-size: 16px;">Thank you for choosing <strong>{self.config.company_name}</strong>! 🚗✨</p>
                            <p style="margin: 10px 0 0 0; font-size: 14px;">Your luxury automotive experience begins now.</p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #f8f9fa; padding: 20px 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="margin: 0 0 10px 0; color: #666; font-size: 13px;">
                                Questions? Contact us at <a href="mailto:{self.config.support_email}" style="color: #007bff; text-decoration: none;">{self.config.support_email}</a>
                            </p>
                            <p style="margin: 0; color: #999; font-size: 12px;">
                                © {datetime.now().year} {self.config.company_name}. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        return html_body

    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via SMTP or console fallback"""
        try:
            if self.config.email_enabled:
                # Create message
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
                msg["To"] = to_email

                # Attach HTML
                html_part = MIMEText(html_body, "html", "utf-8")
                msg.attach(html_part)

                # Send via SMTP
                with smtplib.SMTP(
                    self.config.smtp_host, self.config.smtp_port
                ) as server:
                    if self.config.smtp_use_tls:
                        server.starttls()

                    # Login
                    server.login(self.config.smtp_user, self.config.smtp_password)

                    # Send
                    server.send_message(msg)

                print(f"✅ Email sent successfully to {to_email}")
                return True
            else:
                # Console fallback
                print("\n" + "=" * 70)
                print("📧 EMAIL (Development Mode - No SMTP Configured)")
                print("=" * 70)
                print(f"To: {to_email}")
                print(f"Subject: {subject}")
                print(f"From: {self.config.from_name} <{self.config.from_email}>")
                print("=" * 70)
                print("✅ Email logged to console (configure SMTP to send real emails)")
                print("=" * 70 + "\n")
                return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {e}")
            print("💡 TIP: For Gmail, use an App Password, not your regular password")
            print("   1. Go to: https://myaccount.google.com/apppasswords")
            print("   2. Generate an App Password")
            print("   3. Use it as SMTP_PASSWORD in .env")
            return False
        except Exception as e:
            print(f"❌ Email send error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def send_service_appointment_confirmation(
        self, appointment: Dict[str, Any]
    ) -> bool:
        """Send service appointment confirmation email"""
        try:
            customer_email = appointment.get("customer", {}).get("email")
            if not customer_email:
                print("⚠️ No customer email provided")
                return False

            apt_id = appointment["appointment_id"]
            vehicle = appointment["vehicle"]
            service = appointment["service"]
            provider = appointment["provider"]
            apt_info = appointment["appointment"]
            customer = appointment["customer"]

            # Format datetime
            try:
                from datetime import datetime

                apt_dt = datetime.strptime(
                    f"{apt_info['date']} {apt_info['time']}", "%Y-%m-%d %H:%M"
                )
                formatted_date = apt_dt.strftime("%A, %d %B %Y")
                formatted_time = apt_dt.strftime("%I:%M %p")
            except:
                formatted_date = apt_info["date"]
                formatted_time = apt_info["time"]

            subject = f"✅ Service Appointment Confirmed - {apt_id}"

            # Cost display
            cost_min = service.get("estimated_cost_min", 0)
            cost_max = service.get("estimated_cost_max", 0)
            if cost_max > 0:
                cost_display = f"£{cost_min:,.0f} - £{cost_max:,.0f}"
            else:
                cost_display = "To be confirmed"

            # Build HTML email
            html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
                        
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1a1a1a 0%, #333 100%); color: white; padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; font-size: 32px; font-weight: 700; letter-spacing: 2px;">{self.config.company_name}</h1>
                                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9; letter-spacing: 1px;">LUXURY VEHICLE SERVICE</p>
                            </td>
                        </tr>
                        
                        <!-- Success Badge -->
                        <tr>
                            <td style="padding: 30px; text-align: center;">
                                <div style="display: inline-block; background: #28a745; color: white; padding: 12px 30px; border-radius: 25px; font-size: 18px; font-weight: 600;">
                                    ✅ Service Appointment Confirmed
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Appointment ID -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                                    <table width="100%">
                                        <tr>
                                            <td style="padding: 5px 0;"><strong>Appointment ID:</strong></td>
                                            <td style="padding: 5px 0; text-align: right; font-family: monospace; color: #007bff;">{apt_id}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 5px 0;"><strong>Status:</strong></td>
                                            <td style="padding: 5px 0; text-align: right;"><span style="background: #ffc107; color: #000; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">PENDING</span></td>
                                        </tr>
                                    </table>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Vehicle Details -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">🚗 Your Vehicle</h3>
                                <table width="100%">
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Vehicle:</td>
                                        <td style="padding: 8px 0; text-align: right; font-weight: 600; font-size: 16px;">{vehicle['make']} {vehicle['model']} ({vehicle['year']})</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Current Mileage:</td>
                                        <td style="padding: 8px 0; text-align: right;">{vehicle['mileage']:,} miles</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Service Details -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">🔧 Service Details</h3>
                                <table width="100%">
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Service Type:</td>
                                        <td style="padding: 8px 0; text-align: right; font-weight: 600;">{service['type'].replace('_', ' ').title()}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Urgency:</td>
                                        <td style="padding: 8px 0; text-align: right;"><span style="background: {'#dc3545' if service['urgency'] == 'urgent' else '#ffc107' if service['urgency'] == 'soon' else '#28a745'}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">{service['urgency'].upper()}</span></td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Description:</td>
                                        <td style="padding: 8px 0; text-align: right;">{service['description']}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Duration:</td>
                                        <td style="padding: 8px 0; text-align: right;">{apt_info['duration_estimate']}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Estimated Cost:</td>
                                        <td style="padding: 8px 0; text-align: right; font-size: 18px; color: #28a745; font-weight: 700;">{cost_display}</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Provider Details -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">🏢 Service Provider</h3>
                                <table width="100%">
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Provider:</td>
                                        <td style="padding: 8px 0; text-align: right; font-weight: 600;">{provider['name']}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Type:</td>
                                        <td style="padding: 8px 0; text-align: right;">{"🏆 Tier 1 Official Dealer" if provider['tier'] == 1 else "⭐ Tier 2 Specialist"}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Location:</td>
                                        <td style="padding: 8px 0; text-align: right;">{provider.get('location', 'TBC')}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Distance:</td>
                                        <td style="padding: 8px 0; text-align: right;">{provider.get('distance_miles', 0):.1f} miles from you</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Rating:</td>
                                        <td style="padding: 8px 0; text-align: right;">{"⭐" * int(provider.get('rating', 0))} {provider.get('rating', 0)}/5.0</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #666;">Phone:</td>
                                        <td style="padding: 8px 0; text-align: right; font-weight: 600;">{provider.get('phone', 'TBC')}</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Appointment Time -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff;">
                                    <h3 style="margin: 0 0 15px 0; color: #007bff;">📅 Your Appointment</h3>
                                    <p style="margin: 0; font-size: 18px; font-weight: 600;">
                                        {formatted_date}<br>
                                        <span style="font-size: 24px; color: #007bff;">{formatted_time}</span>
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- What to Bring -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107;">
                                    <h3 style="margin: 0 0 15px 0; color: #856404;">📋 What to Bring</h3>
                                    <ul style="margin: 0; padding-left: 20px; line-height: 1.8; color: #856404;">
                                        <li>Vehicle registration documents</li>
                                        <li>Service history book</li>
                                        <li>List of any additional concerns</li>
                                        <li>Payment method (card/cash accepted)</li>
                                    </ul>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Important Notes -->
                        <tr>
                            <td style="padding: 0 30px 20px 30px;">
                                <div style="background: #f8d7da; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545;">
                                    <h3 style="margin: 0 0 15px 0; color: #721c24;">⏰ Important</h3>
                                    <ul style="margin: 0; padding-left: 20px; line-height: 1.8; color: #721c24;">
                                        <li>Please arrive 10 minutes early</li>
                                        <li>If running late, call {provider.get('phone', 'the provider')}</li>
                                        <li>To reschedule or cancel, contact us 24 hours in advance</li>
                                    </ul>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- CTA Button -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px; text-align: center;">
                                <a href="tel:{provider.get('phone', '')}" style="display: inline-block; background: #007bff; color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-weight: 600; font-size: 16px;">Call Provider</a>
                            </td>
                        </tr>
                        
                        <!-- Thank You -->
                        <tr>
                            <td style="padding: 0 30px 30px 30px; text-align: center; color: #666; line-height: 1.6;">
                                <p style="margin: 0; font-size: 16px;">Thank you for trusting <strong>{self.config.company_name}</strong> with your vehicle care! 🚗✨</p>
                                <p style="margin: 10px 0 0 0; font-size: 14px;">We'll send you a reminder 24 hours before your appointment.</p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background: #f8f9fa; padding: 20px 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                                <p style="margin: 0 0 10px 0; color: #666; font-size: 13px;">
                                    Questions? Contact us at <a href="mailto:{self.config.support_email}" style="color: #007bff; text-decoration: none;">{self.config.support_email}</a>
                                </p>
                                <p style="margin: 0; color: #999; font-size: 12px;">
                                    © {datetime.now().year} {self.config.company_name}. All rights reserved.
                                </p>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

            # Send email
            result = self._send_email(customer_email, subject, html_body)

            if result:
                print(f"✅ Service appointment confirmation sent to {customer_email}")
            else:
                print(f"⚠️ Failed to send service appointment email to {customer_email}")

            return result

        except Exception as e:
            print(f"❌ Service email error: {e}")
            import traceback

            traceback.print_exc()
            return False

        def test_email_configuration(self) -> bool:
            """Test email configuration"""
            print("\n🧪 Testing Email Configuration...")
            print("=" * 70)

            if not self.config.email_enabled:
                print("⚠️ Email not configured - will use console mode")
                return False

            try:
                # Try to connect
                with smtplib.SMTP(
                    self.config.smtp_host, self.config.smtp_port
                ) as server:
                    server.starttls()
                    server.login(self.config.smtp_user, self.config.smtp_password)
                    print("✅ SMTP connection successful!")
                    return True
            except Exception as e:
                print(f"❌ SMTP connection failed: {e}")
                return False


# Singleton
enhanced_email_service = EnhancedEmailService()
