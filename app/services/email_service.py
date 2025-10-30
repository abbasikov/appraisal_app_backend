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