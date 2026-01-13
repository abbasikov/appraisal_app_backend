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
            invitation_url = f"{settings.FRONTEND_URL.rstrip('/')}/setup-password?token={token}"
            
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
    def send_import_completion_email(email: str, project_name: str, imported_count: int, total_found: int = None):
        """Send photo import completion notification email"""
        try:
            subject = f"Photo Import Complete - {project_name}"
            
            total_text = f" out of {total_found}" if total_found and total_found != imported_count else ""
            
            html_body = f"""
            <html>
            <body>
                <h2>Photo Import Complete!</h2>
                <p>Your photo import for project <strong>{project_name}</strong> has been completed successfully.</p>
                <p><strong>Import Summary:</strong></p>
                <ul>
                    <li>Photos imported: {imported_count}{total_text}</li>
                    <li>Status: Complete</li>
                </ul>
                <p>You can now view and work with the imported photos in your project.</p>
                <br>
                <p>Best regards,<br>Appraisal Report Management System</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Photo Import Complete!
            
            Your photo import for project "{project_name}" has been completed successfully.
            
            Import Summary:
            - Photos imported: {imported_count}{total_text}
            - Status: Complete
            
            You can now view and work with the imported photos in your project.
            
            Best regards,
            Appraisal Report Management System
            """
            
            EmailService._send_email(email, subject, text_body, html_body)
            print(f"✅ Import completion email sent to {email}")
            
        except Exception as e:
            print(f"❌ Failed to send import completion email: {e}")
            # Don't raise - email failure shouldn't break the import process
    
    @staticmethod
    def _send_email(to_email: str, subject: str, text_body: str, html_body: str = None):
        """Send email using SMTP"""
        try:
            # Validate configuration
            if not settings.SMTP_USERNAME or settings.SMTP_USERNAME == "Email":
                raise ValueError("SMTP_USERNAME is not configured. Please set your Gmail address in env.txt")
            
            if not settings.SMTP_PASSWORD or settings.SMTP_PASSWORD == "Password":
                raise ValueError("SMTP_PASSWORD is not configured. Please set your Gmail App Password in env.txt")
            
            if not settings.SMTP_FROM_EMAIL or settings.SMTP_FROM_EMAIL == "Email":
                raise ValueError("SMTP_FROM_EMAIL is not configured. Please set your Gmail address in env.txt")
            
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
            
            # Send email with detailed error handling
            print(f"📧 Attempting to send email to {to_email}")
            print(f"   SMTP Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            print(f"   From: {settings.SMTP_FROM_EMAIL}")
            
            # Port 465 uses SSL/TLS, Port 587 uses STARTTLS
            if settings.SMTP_PORT == 465:
                # Use SMTP_SSL for port 465
                print(f"   Using SSL/TLS (port 465)")
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.set_debuglevel(0)  # Set to 1 for verbose SMTP debugging
                    
                    try:
                        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    except smtplib.SMTPAuthenticationError as auth_error:
                        print(f"❌ SMTP Authentication Failed!")
                        print(f"   Error: {auth_error}")
                        print(f"   Username: {settings.SMTP_USERNAME}")
                        raise ValueError(f"SMTP Authentication failed. Error: {auth_error}")
                    
                    server.send_message(msg)
                    print(f"✅ Email sent successfully to {to_email}")
            else:
                # Use STARTTLS for port 587
                print(f"   Using STARTTLS (port 587)")
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.set_debuglevel(0)  # Set to 1 for verbose SMTP debugging
                    server.starttls()
                    
                    try:
                        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    except smtplib.SMTPAuthenticationError as auth_error:
                        print(f"❌ SMTP Authentication Failed!")
                        print(f"   Error: {auth_error}")
                        print(f"   Username: {settings.SMTP_USERNAME}")
                        raise ValueError(f"SMTP Authentication failed. Error: {auth_error}")
                    
                    server.send_message(msg)
                    print(f"✅ Email sent successfully to {to_email}")
                
        except ValueError as ve:
            print(f"❌ Configuration error: {ve}")
            raise ve
        except smtplib.SMTPException as smtp_error:
            print(f"❌ SMTP error: {smtp_error}")
            raise smtp_error
        except Exception as e:
            print(f"❌ Unexpected error sending email: {type(e).__name__}: {e}")
            raise e