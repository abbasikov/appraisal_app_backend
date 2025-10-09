import asyncio
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.celery_app import celery_app
from app.api.v1.api import api_router
from app.db.init_db import create_tables
from app.core.scheduler import cleanup_task

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

# Set specific loggers to DEBUG level
logging.getLogger('app.utils.template_converter').setLevel(logging.DEBUG)
logging.getLogger('app.services.template_service').setLevel(logging.DEBUG)
logging.getLogger('uvicorn').setLevel(logging.INFO)
logging.getLogger('uvicorn.access').setLevel(logging.INFO)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Appraisal Report Management System API"
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    logger = logging.getLogger(__name__)
    logger.info("Starting Appraisal App API...")
    logger.info("Logging configured - DEBUG level enabled")
    create_tables()
    # Start background cleanup task
    asyncio.create_task(cleanup_task())
    logger.info("Startup completed successfully")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Appraisal App API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {"status": "healthy", "celery": "configured"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=300,  # 5 minutes
        timeout_graceful_shutdown=30
    )