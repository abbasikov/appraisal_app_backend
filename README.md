# Appraisal Report Backend

FastAPI backend for the Appraisal Report Management System with JWT authentication, role-based access control, and comprehensive API endpoints.

## 🚀 Quick Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- SMTP Email Account (Gmail recommended)

### Installation
```bash
# Navigate to backend directory
cd appraisal_app_backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and email credentials

# Setup database
python migrate_db.py

# Create admin user
python create_admin.py

# Start server
python main.py
```

## 🔧 Configuration

### Environment Variables (.env)
```env
# Database
DATABASE_URL=postgresql://username:password@localhost/appraisal_db

# Security
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (Gmail setup)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password
SMTP_FROM_EMAIL=your-email@gmail.com

# Application
APP_NAME="Appraisal Report Management"
DEBUG=True
```

### Gmail App Password Setup
1. Enable 2-Factor Authentication on Gmail
2. Go to Google Account > Security > App Passwords
3. Generate app password for "Mail"
4. Use this password in SMTP_PASSWORD

## 📁 Project Structure

```
appraisal_app_backend/
├── app/
│   ├── api/v1/              # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication & MFA
│   │   ├── clients.py       # Client management
│   │   ├── projects.py      # Project management
│   │   └── users.py         # User management
│   ├── core/                # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py        # App settings
│   │   ├── database.py      # Database connection
│   │   └── security.py      # Security utilities
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py          # User model with MFA
│   │   ├── client.py        # Client model
│   │   ├── project.py       # Project model
│   │   └── activity_log.py  # Audit logging
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py          # User schemas
│   │   ├── client.py        # Client schemas
│   │   ├── project.py       # Project schemas
│   │   └── auth.py          # Auth schemas
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py  # Authentication logic
│   │   ├── client_service.py # Client operations
│   │   └── project_service.py # Project operations
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── email.py         # Email utilities
│       └── security.py     # Security helpers
├── create_admin.py          # Admin creation script
├── migrate_db.py           # Database migration
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## 🔐 Authentication System

### User Roles
- **admin**: Full system access, user management
- **editor**: Create/edit clients and projects
- **reader**: View-only access

### Features
- JWT token authentication
- Role-based access control
- Email verification for new users
- Two-Factor Authentication (TOTP)
- Password hashing with bcrypt
- Rate limiting protection

### MFA Implementation
- QR code generation for authenticator apps
- TOTP verification (RFC 6238)
- Enable/disable functionality
- Backup codes (future enhancement)

## 📊 Database Models

### User Model
```python
class User(Base):
    id: int (Primary Key)
    username: str (Unique)
    email: str (Unique)
    hashed_password: str
    role: UserRole (admin/editor/reader)
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    mfa_secret: str (Optional)
    created_at: datetime
    updated_at: datetime
```

### Client Model
```python
class Client(Base):
    id: int (Primary Key)
    name: str (Required)
    company: str (Optional)
    email: str (Optional)
    phone: str (Optional)
    address: str (Optional)
    city: str (Optional)
    state: str (Optional)
    zip_code: str (Optional)
    attorney_name: str (Optional)
    attorney_email: str (Optional)
    attorney_phone: str (Optional)
    case_name: str (Optional)
    case_number: str (Optional)
    date_of_death: date (Optional)
    notes: text (Optional)
    is_active: bool (Default: True)
    created_at: datetime
    updated_at: datetime
```

### Project Model
```python
class Project(Base):
    id: int (Primary Key)
    name: str (Required)
    project_type: ProjectType (DIVORCE/ESTATE)
    client_id: int (Foreign Key to Client)
    assigned_user_id: int (Foreign Key to User, Optional)
    start_date: date (Optional)
    deadline: date (Optional)
    completion_date: date (Optional)
    status: ProjectStatus (PENDING/IN_PROGRESS/COMPLETED/CANCELLED)
    notes: text (Optional)
    is_active: bool (Default: True)
    created_at: datetime
    updated_at: datetime
```

## 🛠 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/verify-email` - Email verification
- `POST /api/v1/auth/setup-mfa` - Setup 2FA
- `POST /api/v1/auth/verify-mfa` - Verify 2FA code
- `POST /api/v1/auth/disable-mfa` - Disable 2FA

### Users
- `GET /api/v1/users/me` - Current user info
- `PUT /api/v1/users/me` - Update profile
- `GET /api/v1/users/` - List users (Admin only)

### Clients
- `GET /api/v1/clients/` - List clients
- `POST /api/v1/clients/` - Create client
- `GET /api/v1/clients/{id}` - Get client
- `PUT /api/v1/clients/{id}` - Update client
- `DELETE /api/v1/clients/{id}` - Delete client (Admin only)

### Projects
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project (Admin only)

## 🔄 Database Migration

### Initial Setup
```bash
python migrate_db.py
```

### Adding New Migrations
1. Modify models in `app/models/`
2. Update `migrate_db.py` with new table/column changes
3. Run migration: `python migrate_db.py`

### Migration Script Features
- Creates all tables if they don't exist
- Adds new columns safely
- Handles data type changes
- Preserves existing data

## 👤 Admin Management

### Create Admin User
```bash
python create_admin.py
```

### Admin Capabilities
- Full CRUD access to all resources
- User management and role assignment
- System configuration access
- Activity log monitoring
- No email verification required

## 📧 Email System

### SMTP Configuration
- Supports Gmail, Outlook, and custom SMTP
- Email verification for new users
- Password reset functionality (future)
- Notification system (future)

### Email Templates
- Welcome email with verification code
- MFA setup instructions
- Account status notifications

## 🔒 Security Features

### Password Security
- bcrypt hashing with salt
- Minimum password requirements
- Password change tracking

### API Security
- JWT token validation
- Role-based endpoint protection
- Rate limiting on sensitive endpoints
- CORS configuration
- Input validation and sanitization

### Audit Logging
- All user actions logged
- Database change tracking
- Failed login attempts
- Admin activity monitoring

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

### Test Structure
```
tests/
├── test_auth.py        # Authentication tests
├── test_clients.py     # Client API tests
├── test_projects.py    # Project API tests
└── test_models.py      # Database model tests
```

## 🚀 Production Deployment

### Environment Setup
```env
DEBUG=False
SECRET_KEY=production-secret-key-here
DATABASE_URL=postgresql://user:pass@prod-db:5432/appraisal_db
SMTP_SERVER=smtp.sendgrid.net  # Or AWS SES
```

### Deployment Checklist
- [ ] Set DEBUG=False
- [ ] Use production database
- [ ] Configure production SMTP
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Configure reverse proxy
- [ ] Set up monitoring
- [ ] Regular backups

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Monitoring & Logging

### Application Logs
- Request/response logging
- Error tracking
- Performance metrics
- Security events

### Health Checks
- Database connectivity
- Email service status
- API endpoint health

## 🔧 Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes
- Write comprehensive tests

### Adding New Features
1. Create/update models in `app/models/`
2. Add schemas in `app/schemas/`
3. Implement service logic in `app/services/`
4. Create API endpoints in `app/api/v1/`
5. Write tests
6. Update documentation

### Database Changes
1. Modify model classes
2. Update migration script
3. Test migration on development database
4. Document changes

## 📞 Support

### Common Issues
- **Database connection**: Check DATABASE_URL format
- **Email not sending**: Verify SMTP credentials and app password
- **Authentication errors**: Check SECRET_KEY and token expiration
- **Permission denied**: Verify user roles and endpoint permissions

### Debugging
```bash
# Enable debug mode
export DEBUG=True

# Check logs
tail -f app.log

# Test database connection
python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```