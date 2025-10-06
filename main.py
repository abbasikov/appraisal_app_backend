import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.celery_app import celery_app
from app.api.v1.api import api_router
from app.db.init_db import create_tables
from app.core.scheduler import cleanup_task

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Appraisal Report Management System API"
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    # Start background cleanup task
    asyncio.create_task(cleanup_task())

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