# Appraisal Report Backend

FastAPI backend for the Appraisal Report Management System with template processing and report generation.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Virtual Environment

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
python migrate_db.py
python migrate_template_db.py

# Create admin account
python create_admin.py

# Start server
python main.py
```

## 📁 Project Structure

```
app/
├── api/v1/endpoints/     # API routes
│   ├── auth.py          # Authentication
│   ├── clients.py       # Client management
│   ├── projects.py      # Project management
│   ├── templates.py     # Template management
│   └── users.py         # User management
├── core/                # Configuration
├── models/              # SQLAlchemy models
│   ├── user.py         # User with MFA
│   ├── client.py       # Client data
│   ├── project.py      # Project data
│   ├── template.py     # Template storage
│   └── report.py       # Generated reports
├── schemas/             # Pydantic schemas
├── services/            # Business logic
│   ├── template_service.py
│   └── client_service.py
└── utils/               # Utilities
    └── template_converter.py  # Word processing
```

## 🔧 Features

### Template Management
- **Upload**: Word (.docx) template upload with validation
- **Conversion**: Automatic field extraction and fillable template creation
- **Field Mapping**: Configure field types, defaults, and validation
- **Report Generation**: Merge templates with project data

### Authentication & Security
- **JWT Tokens**: Secure API authentication
- **Role-Based Access**: Admin, Editor, Reader permissions
- **MFA Support**: TOTP-based two-factor authentication
- **Input Validation**: Comprehensive request validation

### Database Models
- **Users**: Authentication with roles and MFA
- **Clients**: Client information with attorney details
- **Projects**: Appraisal projects with status tracking
- **Templates**: Word template storage with field mappings
- **Reports**: Generated report tracking

## 🌐 API Endpoints

### Authentication
- `POST /auth/signin` - User login
- `POST /auth/signup` - User registration
- `GET /auth/me` - Current user info

### Templates
- `GET /templates/` - List templates
- `POST /templates/upload` - Upload template
- `GET /templates/{id}` - Get template details
- `PUT /templates/{id}/mappings` - Update field mappings
- `POST /templates/{id}/generate` - Generate report
- `GET /templates/{id}/download` - Download template

### Projects & Clients
- `GET /projects/` - List projects
- `POST /projects/` - Create project
- `GET /clients/` - List clients
- `POST /clients/` - Create client

## 🔒 Security

### Role-Based Permissions
- **Admin**: Full system access
- **Editor**: Create/edit clients, projects, templates
- **Reader**: View-only access

### File Security
- File type validation (.docx only)
- Size limits (10MB max)
- Secure file storage
- Path traversal protection

## 📊 Configuration

### Environment Variables
```env
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=your-secret-key
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Dependencies
- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **python-docx**: Word document processing
- **PyJWT**: JWT token handling
- **bcrypt**: Password hashing

## 🧪 Testing

```bash
# Run tests
pytest

# Test API endpoints
python test_api.py

# Check database
python check_db.py
```

## 📈 Performance

- **Async Support**: FastAPI async endpoints
- **Database Pooling**: SQLAlchemy connection pooling
- **File Streaming**: Efficient file upload/download
- **Caching**: Template and field mapping caching