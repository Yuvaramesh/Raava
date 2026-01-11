"""
Enhanced Email Service - With Order and Appointment Confirmations
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
    """Email service with templates for orders and appointments"""

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
            html_body = self._build_order_confirmation_html(
                order, vehicle, customer, finance
            )

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

    def send_appointment_confirmation(self, appointment: Dict[str, Any]) -> bool:
        """Send appointment confirmation email"""
        try:
            customer_email = appointment.get("customer", {}).get("email")
            if not customer_email:
                print("⚠️ No customer email provided for appointment")
                return False

            subject = f"✅ Service Appointment Confirmed - {appointment.get('appointment_id')}"
            html_body = self._build_appointment_confirmation_html(appointment)

            result = self._send_email(customer_email, subject, html_body)

            if result:
                print(f"✅ Appointment confirmation sent to {customer_email}")
            else:
                print(f"⚠️ Failed to send appointment email to {customer_email}")

            return result

        except Exception as e:
            print(f"❌ Appointment email error: {e}")
            import traceback

            traceback.print_exc()
            return False

    # Add this method to the EnhancedEmailService class in enhanced_email_service.py

    def send_service_appointment_confirmation(
        self, appointment: Dict[str, Any]
    ) -> bool:
        """Send service appointment confirmation email"""
        try:
            customer_email = appointment.get("customer", {}).get("email")
            if not customer_email:
                print("⚠️ No customer email provided")
                return False

            vehicle = appointment.get("vehicle", {})
            service = appointment.get("service", {})
            customer = appointment.get("customer", {})
            provider = appointment.get("provider", {})
            apt = appointment.get("appointment", {})

            subject = f"✅ Service Appointment Confirmed - {appointment.get('appointment_id')}"

            # Build email body
            html_body = self._build_service_appointment_html(
                appointment, vehicle, service, customer, provider, apt
            )

            # Send email
            result = self._send_email(customer_email, subject, html_body)

            if result:
                print(f"✅ Service confirmation sent to {customer_email}")
            else:
                print(f"⚠️ Failed to send email to {customer_email}")

            return result

        except Exception as e:
            print(f"❌ Email error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _build_service_appointment_html(
        self,
        appointment: Dict[str, Any],
        vehicle: Dict[str, Any],
        service: Dict[str, Any],
        customer: Dict[str, Any],
        provider: Dict[str, Any],
        apt: Dict[str, Any],
    ) -> str:
        """Build service appointment HTML email"""

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
                            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9; letter-spacing: 1px;">SERVICE BOOKING PLATFORM</p>
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
                    
                    <!-- Appointment ID Box -->
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                                <table width="100%">
                                    <tr>
                                        <td style="padding: 5px 0;"><strong>Appointment ID:</strong></td>
                                        <td style="padding: 5px 0; text-align: right; font-family: monospace; color: #007bff;">{appointment.get('appointment_id')}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px 0;"><strong>Booked:</strong></td>
                                        <td style="padding: 5px 0; text-align: right;">{appointment.get('created_at', datetime.utcnow()).strftime('%d %B %Y, %H:%M')}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px 0;"><strong>Status:</strong></td>
                                        <td style="padding: 5px 0; text-align: right;"><span style="background: #ffc107; color: #000; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">PENDING</span></td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Appointment Date/Time - PROMINENT -->
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <div style="background: #007bff; color: white; padding: 25px; border-radius: 8px; text-align: center;">
                                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">APPOINTMENT DATE & TIME</div>
                                <div style="font-size: 24px; font-weight: 700;">{apt.get('formatted', 'TBD')}</div>
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
                                    <td style="padding: 8px 0; color: #666;">Mileage:</td>
                                    <td style="padding: 8px 0; text-align: right;">{vehicle.get('mileage', 0):,} miles</td>
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
                                    <td style="padding: 8px 0; text-align: right; font-weight: 600;">{service.get('type', '').replace('_', ' ').title()}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Description:</td>
                                    <td style="padding: 8px 0; text-align: right;">{service.get('description', '')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Urgency:</td>
                                    <td style="padding: 8px 0; text-align: right;">{service.get('urgency', 'routine').title()}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Service Provider -->
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">🏢 Service Provider</h3>
                            <table width="100%">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Provider:</td>
                                    <td style="padding: 8px 0; text-align: right; font-weight: 600; font-size: 16px;">{provider.get('name', '')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Location:</td>
                                    <td style="padding: 8px 0; text-align: right;">{provider.get('location', '')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Phone:</td>
                                    <td style="padding: 8px 0; text-align: right;"><a href="tel:{provider.get('phone', '')}" style="color: #007bff; text-decoration: none;">{provider.get('phone', '')}</a></td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Rating:</td>
                                    <td style="padding: 8px 0; text-align: right;">{provider.get('rating', 0)}⭐</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Estimated Cost:</td>
                                    <td style="padding: 8px 0; text-align: right; font-size: 20px; color: #28a745; font-weight: 700;">£{provider.get('estimated_cost', 0):,}</td>
                                </tr>
                            </table>
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
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Postcode:</td>
                                    <td style="padding: 8px 0; text-align: right;">{customer.get('postcode')}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- What to Bring -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff;">
                                <h3 style="margin: 0 0 15px 0; color: #007bff;">📋 What to Bring</h3>
                                <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                                    <li>Vehicle service book/history</li>
                                    <li>Valid driving licence</li>
                                    <li>Proof of address</li>
                                    <li>Any warranty documents</li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Important Notes -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107;">
                                <h3 style="margin: 0 0 15px 0; color: #856404;">⚠️ Important Information</h3>
                                <ul style="margin: 0; padding-left: 20px; line-height: 1.8; color: #856404;">
                                    <li>{provider.get('name')} will call you 24 hours before your appointment</li>
                                    <li>Please arrive 10 minutes early</li>
                                    <li>Service duration: 2-4 hours (depending on service type)</li>
                                    <li>To reschedule: Call {provider.get('phone')} at least 24 hours in advance</li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- CTA Buttons -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <table width="100%">
                                <tr>
                                    <td style="padding: 10px; text-align: center;">
                                        <a href="tel:{provider.get('phone', '')}" style="display: inline-block; background: #007bff; color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-weight: 600; font-size: 16px;">📞 Call Provider</a>
                                    </td>
                                    <td style="padding: 10px; text-align: center;">
                                        <a href="mailto:{self.config.support_email}" style="display: inline-block; background: #28a745; color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-weight: 600; font-size: 16px;">💬 Contact Support</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Thank You Message -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center; color: #666; line-height: 1.6;">
                            <p style="margin: 0; font-size: 16px;">Thank you for choosing <strong>{self.config.company_name}</strong> Service! 🔧✨</p>
                            <p style="margin: 10px 0 0 0; font-size: 14px;">We'll take excellent care of your {vehicle.get('make')}!</p>
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

    def _build_order_confirmation_html(
        self,
        order: Dict[str, Any],
        vehicle: Dict[str, Any],
        customer: Dict[str, Any],
        finance: Dict[str, Any],
    ) -> str:
        """Build HTML email body for orders"""

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
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a1a1a 0%, #333 100%); color: white; padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; font-size: 32px; font-weight: 700; letter-spacing: 2px;">{self.config.company_name}</h1>
                            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9; letter-spacing: 1px;">LUXURY AUTOMOTIVE PLATFORM</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <div style="display: inline-block; background: #28a745; color: white; padding: 12px 30px; border-radius: 25px; font-size: 18px; font-weight: 600;">
                                ✅ Order Confirmed
                            </div>
                        </td>
                    </tr>
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
                                        <td style="padding: 5px 0; text-align: right;">{datetime.now().strftime('%d %B %Y, %H:%M')}</td>
                                    </tr>
                                </table>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">🚗 Vehicle Details</h3>
                            <table width="100%">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Vehicle:</td>
                                    <td style="padding: 8px 0; text-align: right; font-weight: 600; font-size: 16px;">{vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('year')})</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Price:</td>
                                    <td style="padding: 8px 0; text-align: right; font-size: 20px; color: #28a745; font-weight: 700;">£{vehicle.get('price', 0):,}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            {finance_section}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center; color: #666;">
                            <p style="margin: 0; font-size: 16px;">Thank you for choosing <strong>{self.config.company_name}</strong>! 🚗✨</p>
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

    def _build_appointment_confirmation_html(self, appointment: Dict[str, Any]) -> str:
        """Build HTML email for appointment confirmation"""

        vehicle = appointment.get("vehicle", {})
        customer = appointment.get("customer", {})
        provider = appointment.get("provider", {})
        service = appointment.get("service", {})
        apt_info = appointment.get("appointment", {})

        # Format date/time
        try:
            apt_dt = datetime.strptime(
                f"{apt_info.get('date')} {apt_info.get('time')}", "%Y-%m-%d %H:%M"
            )
            formatted_date = apt_dt.strftime("%A, %d %B %Y")
            formatted_time = apt_dt.strftime("%I:%M %p")
        except:
            formatted_date = apt_info.get("date", "")
            formatted_time = apt_info.get("time", "")

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
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; font-size: 28px;">✅ Service Appointment Confirmed</h1>
                            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Your vehicle service has been scheduled</p>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 30px;">
                            <div style="background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin-bottom: 20px;">
                                <h3 style="margin: 0 0 10px 0; color: #856404;">📅 Appointment Date & Time</h3>
                                <p style="font-size: 18px; margin: 0; font-weight: bold; color: #333;">{formatted_date}</p>
                                <p style="font-size: 18px; margin: 5px 0 0 0; font-weight: bold; color: #333;">{formatted_time}</p>
                            </div>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">📋 Appointment Details</h3>
                            <table width="100%">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Appointment ID:</td>
                                    <td style="padding: 8px 0; text-align: right; font-family: monospace; color: #667eea; font-weight: 600;">{appointment.get('appointment_id')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Service Type:</td>
                                    <td style="padding: 8px 0; text-align: right;">{service.get('type', '').replace('_', ' ').title()}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Status:</td>
                                    <td style="padding: 8px 0; text-align: right;"><span style="background: #28a745; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">CONFIRMED</span></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">🚗 Vehicle Information</h3>
                            <table width="100%">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Make & Model:</td>
                                    <td style="padding: 8px 0; text-align: right; font-weight: 600;">{vehicle.get('make')} {vehicle.get('model')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Year:</td>
                                    <td style="padding: 8px 0; text-align: right;">{vehicle.get('year')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Current Mileage:</td>
                                    <td style="padding: 8px 0; text-align: right;">{vehicle.get('mileage', 0):,} miles</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 0 30px 20px 30px;">
                            <h3 style="margin: 0 0 15px 0; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">🏢 Service Provider</h3>
                            <table width="100%">
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Name:</td>
                                    <td style="padding: 8px 0; text-align: right; font-weight: 600;">{provider.get('name')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Location:</td>
                                    <td style="padding: 8px 0; text-align: right;">{provider.get('location')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Rating:</td>
                                    <td style="padding: 8px 0; text-align: right;">⭐ {provider.get('rating')}/5</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #666;">Phone:</td>
                                    <td style="padding: 8px 0; text-align: right;">{provider.get('phone')}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="background: #e8f4f8; padding: 20px; border-radius: 8px; border-left: 4px solid #17a2b8;">
                                <h3 style="margin: 0 0 10px 0; color: #0c5460;">📝 What to Bring:</h3>
                                <ul style="margin: 0; padding-left: 20px; color: #0c5460;">
                                    <li>Vehicle registration documents</li>
                                    <li>Service history (if available)</li>
                                    <li>Any warranty documentation</li>
                                    <li>Payment method</li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center;">
                            <p style="margin: 0; color: #666; font-size: 14px;"><strong>Need to reschedule?</strong></p>
                            <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">Contact us at {self.config.support_email}</p>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="background: #f8f9fa; padding: 20px 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="margin: 0; color: #666; font-size: 14px;">Thank you for trusting {self.config.company_name} 🚗</p>
                            <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">© {datetime.now().year} {self.config.company_name}. All rights reserved.</p>
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
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
                msg["To"] = to_email

                html_part = MIMEText(html_body, "html", "utf-8")
                msg.attach(html_part)

                with smtplib.SMTP(
                    self.config.smtp_host, self.config.smtp_port
                ) as server:
                    if self.config.smtp_use_tls:
                        server.starttls()
                    server.login(self.config.smtp_user, self.config.smtp_password)
                    server.send_message(msg)

                print(f"✅ Email sent successfully to {to_email}")
                return True
            else:
                print("\n" + "=" * 70)
                print("📧 EMAIL (Development Mode - No SMTP Configured)")
                print("=" * 70)
                print(f"To: {to_email}")
                print(f"Subject: {subject}")
                print("=" * 70)
                print("✅ Email logged to console (configure SMTP to send real emails)")
                print("=" * 70 + "\n")
                return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {e}")
            print("💡 TIP: For Gmail, use an App Password")
            return False
        except Exception as e:
            print(f"❌ Email send error: {e}")
            import traceback

            traceback.print_exc()
            return False


# Singleton
enhanced_email_service = EnhancedEmailService()
