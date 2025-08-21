import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        text = msg.as_string()
        server.sendmail(settings.SMTP_FROM_EMAIL, to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_verification_email(to_email: str, code: str) -> bool:
    subject = "Email Verification - Appraisal App"
    body = f"""
    <html>
        <body>
            <h2>Email Verification</h2>
            <p>Your verification code is: <strong>{code}</strong></p>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
    </html>
    """
    return send_email(to_email, subject, body)

def send_password_reset_email(to_email: str, code: str) -> bool:
    subject = "Password Reset - Appraisal App"
    body = f"""
    <html>
        <body>
            <h2>Password Reset</h2>
            <p>Your password reset code is: <strong>{code}</strong></p>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
    </html>
    """
    return send_email(to_email, subject, body)