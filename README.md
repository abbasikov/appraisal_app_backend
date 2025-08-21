# Appraisal App Backend

FastAPI backend with JWT authentication and email verification.

## Quick Start

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database
createdb appraisal_db
python migrate_db.py

# Create admin
python create_admin.py

# Run
python main.py
```

Server runs at: http://localhost:8000

## Environment Setup

Copy `.env.example` to `.env` and configure:
```env
DATABASE_URL=postgresql://postgres:12345@localhost/appraisal_db
SECRET_KEY=your-secret-key
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

## Features

- **Authentication**: JWT tokens, email verification with 6-digit codes
- **User Roles**: Admin (no verification), Appraiser, Client (verification required)
- **Email System**: SMTP integration with rate limiting
- **Security**: Password hashing, token expiration, role-based access

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/signin` - Login (username or email)
- `POST /api/v1/auth/verify-email` - Email verification
- `POST /api/v1/auth/password-reset` - Password reset

### User Management
- `GET /api/v1/auth/me` - Current user info
- `GET /api/v1/users/profile` - User profile

## Admin Account

Admin accounts bypass email verification and have full access:
```bash
python create_admin.py  # Interactive creation
```

## Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
