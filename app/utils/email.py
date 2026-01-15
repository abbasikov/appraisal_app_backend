import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        # Validate configuration
        if not settings.SMTP_USERNAME or settings.SMTP_USERNAME == "Email":
            print("❌ SMTP_USERNAME is not configured. Please set your Gmail address in env.txt")
            return False
        
        if not settings.SMTP_PASSWORD or settings.SMTP_PASSWORD == "Password":
            print("❌ SMTP_PASSWORD is not configured. Please set your Gmail App Password in env.txt")
            return False
        
        if not settings.SMTP_FROM_EMAIL or settings.SMTP_FROM_EMAIL == "Email":
            print("❌ SMTP_FROM_EMAIL is not configured. Please set your Gmail address in env.txt")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Reply-To'] = settings.SMTP_FROM_EMAIL
        msg['Return-Path'] = settings.SMTP_FROM_EMAIL
        msg['Date'] = email.utils.formatdate(localtime=True)
        msg['Message-ID'] = email.utils.make_msgid(domain=settings.SMTP_FROM_EMAIL.split('@')[1])
        msg['X-Mailer'] = 'Appraisal App Email Service'
        
        msg.attach(MIMEText(body, 'html'))
        
        print(f"📧 Sending email to {to_email}")
        print(f"   Subject: {subject}")
        print(f"   From: {settings.SMTP_FROM_EMAIL}")
        
        # Port 465 uses SSL/TLS, Port 587 uses STARTTLS
        if settings.SMTP_PORT == 465:
            print(f"   Using SSL/TLS (port 465)")
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            print(f"   Using STARTTLS (port 587)")
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.starttls()
        
        try:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"❌ SMTP Authentication Failed!")
            print(f"   Error: {auth_error}")
            print(f"   Username: {settings.SMTP_USERNAME}")
            server.quit()
            return False
        
        text = msg.as_string()
        server.sendmail(settings.SMTP_FROM_EMAIL, to_email, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except smtplib.SMTPException as smtp_error:
        print(f"❌ SMTP error: {smtp_error}")
        return False
    except Exception as e:
        print(f"❌ Failed to send email: {type(e).__name__}: {e}")
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