# Appraisal App Backend

FastAPI backend for the Appraisal Report Management System with JWT authentication and OTP MFA.

## Quick Start

```bash
# 1. Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
createdb appraisal_db

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 5. Start server
python main.py

# 6. Create admin user
python create_admin.py
```

## Environment Configuration

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost/appraisal_db

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_HOSTS=http://localhost:3000,http://localhost:5173

# SMTP (for email verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

## Features

- **JWT Authentication**: Secure token-based authentication
- **Two-Factor Authentication**: TOTP MFA with QR code setup
- **Email Verification**: SMTP-based email verification system
- **Role-based Access Control**: Admin, Editor, Reader roles
- **Password Reset**: Secure password reset with email codes
- **API Documentation**: Auto-generated Swagger/OpenAPI docs

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/signin` - Login (returns token or OTP requirement)
- `POST /api/v1/auth/signin-mfa` - MFA login with OTP code
- `POST /api/v1/auth/verify-email` - Email verification
- `GET /api/v1/auth/me` - Get current user info

### Two-Factor Authentication
- `GET /api/v1/otp/status` - Check OTP status
- `POST /api/v1/otp/setup` - Generate QR code for setup
- `POST /api/v1/otp/enable` - Enable OTP after verification
- `POST /api/v1/otp/disable` - Disable OTP

### Password Reset
- `POST /api/v1/auth/password-reset` - Request reset code
- `POST /api/v1/auth/password-reset/confirm` - Reset with code

## User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **admin** | System administrator | Full access to all features |
| **editor** | Content editor | Can manage properties and appraisals |
| **reader** | Read-only user | Can view appraisals only |

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `password_hash` - Bcrypt hashed password
- `role` - User role (admin/editor/reader)
- `is_active` - Account status
- `is_email_verified` - Email verification status
- `otp_enabled` - 2FA status
- `otp_secret` - TOTP secret key
- `last_login` - Last login timestamp

## Security Features

- **Password Hashing**: Bcrypt with salt
- **JWT Tokens**: Secure token-based authentication
- **TOTP MFA**: Time-based one-time passwords
- **Email Verification**: Prevents fake account creation
- **Rate Limiting**: Built-in request rate limiting
- **CORS Protection**: Configurable CORS origins

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Database migrations (if schema changes)
python migrate_db.py
```

## Production Deployment

1. **Environment**: Set production environment variables
2. **Database**: Use production PostgreSQL instance
3. **SMTP**: Configure production email service
4. **Security**: Use strong SECRET_KEY and HTTPS
5. **Reverse Proxy**: Use nginx or similar
6. **SSL**: Configure SSL certificates

## Troubleshooting

### Database Issues
```bash
# Reset database
dropdb appraisal_db
createdb appraisal_db
python main.py  # Auto-creates tables
```

### OTP Issues
- Ensure phone/server time sync
- Delete old authenticator entries before re-setup
- Check TOTP secret matches between app and database

### Email Issues
- Verify SMTP credentials
- Check firewall/network restrictions
- Use app-specific passwords for Gmail
