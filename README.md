# Appraisal Report Management System - Backend

FastAPI backend with PostgreSQL database, JWT authentication, and Dropbox integration.

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Dropbox App (for photo import)

### Setup
```bash
# Clone and navigate
cd appraisal_app_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Setup database
python migrate_db.py

# Create admin user
python create_admin.py

# Start server
python main.py
```

## Configuration

### Environment Variables (.env)
```env
# Database
DATABASE_URL=postgresql://username:password@localhost/appraisal_db

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Gmail recommended)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com

# Dropbox Integration
DROPBOX_APP_KEY=your_dropbox_app_key
DROPBOX_APP_SECRET=your_dropbox_app_secret
DROPBOX_ACCESS_TOKEN=your_dropbox_access_token
```

### Dropbox Setup
1. Create app at https://www.dropbox.com/developers/apps
2. Enable permissions: `files.content.read`, `files.metadata.read`, `sharing.read`
3. Generate access token
4. Add credentials to .env

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
- `POST /api/v1/auth/login` - Authentication
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/projects/{id}/dropbox-links` - Add Dropbox folders
- `POST /api/v1/projects/{id}/import-photos` - Import photos from Dropbox
- `GET /api/v1/projects/{id}/photos` - List project photos

## Features

### Authentication
- JWT token-based authentication
- Two-factor authentication (TOTP)
- Role-based access control (Admin, Editor, Reader)
- Email verification for new users

### Dropbox Integration
- Shared folder photo import
- Automatic ZIP extraction
- Thumbnail generation (150x150px)
- EXIF date extraction
- Authenticated thumbnail serving

### Database Models
- Users with MFA support
- Clients and Projects
- Photos with metadata
- Activity logging

## Project Structure
```
app/
├── api/v1/endpoints/     # API routes
├── core/                 # Configuration
├── models/              # Database models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
└── utils/               # Utilities
```

## Development

### Database Migration
```bash
python migrate_db.py
```

### Create Admin User
```bash
python create_admin.py
```

### Run Tests
```bash
pytest
```