# Appraisal App Backend

FastAPI backend for the Appraisal Report Management System.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database and secret key configuration
```

4. Set up PostgreSQL database:
```bash
# Create database
createdb appraisal_db
```

5. Run the application:
```bash
python main.py
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/

## Available Endpoints

- `/api/v1/users` - User management
- `/api/v1/properties` - Property data
- `/api/v1/appraisals` - Appraisal workflows
- `/api/v1/reports` - Report generation

## Project Structure

```
app/
├── api/v1/
│   ├── endpoints/   # API route handlers
│   └── api.py       # Main API router
├── core/            # Core configuration
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── services/        # Business logic
├── utils/           # Utility functions
└── db/              # Database configuration
```

## Environment Variables

Required variables in `.env`:
- `SECRET_KEY` - JWT secret key
- `DATABASE_URL` - PostgreSQL connection string
- `ALLOWED_HOSTS` - CORS allowed origins

## Development

- Use `uvicorn main:app --reload` for auto-reload during development
- Run tests with `pytest`
- Format code with `black` and `isort`