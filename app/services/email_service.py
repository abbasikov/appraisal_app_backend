import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

class EmailService:
    
    @staticmethod
    def send_invitation_email(email: str, first_name: str, token: str):
        """Send invitation email to new user"""
        try:
            # Create invitation URL
            invitation_url = f"http://localhost:5173/setup-password?token={token}"
            
            # Email content
            subject = "Invitation to Appraisal Report Management System"
            
            html_body = f"""
            <html>
            <body>
                <h2>You're Invited!</h2>
                <p>Hello {first_name},</p>
                <p>You have been invited to join the Appraisal Report Management System.</p>
                <p>Click the link below to set up your password and activate your account:</p>
                <p><a href="{invitation_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Set Up Password</a></p>
                <p>This invitation will expire in 48 hours.</p>
                <p>If you didn't expect this invitation, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Appraisal Report Management Team</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Hello {first_name},
            
            You have been invited to join the Appraisal Report Management System.
            
            Please visit the following link to set up your password:
            {invitation_url}
            
            This invitation will expire in 48 hours.
            
            Best regards,
            Appraisal Report Management Team
            """
            
            # Send email
            EmailService._send_email(email, subject, text_body, html_body)
            print(f"✅ Invitation email sent to {email}")
            
        except Exception as e:
            print(f"❌ Failed to send invitation email: {e}")
            raise e
    
    @staticmethod
    def _send_email(to_email: str, subject: str, text_body: str, html_body: str = None):
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = to_email
            
            # Add text part
            text_part = MIMEText(text_body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
                
        except Exception as e:
            print(f"❌ SMTP error: {e}")
            raise e