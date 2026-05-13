from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Appraisal App API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour; idle logout enforced client-side, active users get refreshed tokens
    
    DATABASE_URL: str
    ALLOWED_HOSTS: str = "http://localhost:3000,http://localhost:5173"
    FRONTEND_URL: str = "http://localhost:5173"
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]
    
    MAX_FILE_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # SMTP Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    
    # Dropbox Configuration
    DROPBOX_APP_KEY: str = ""
    DROPBOX_APP_SECRET: str = ""
    DROPBOX_ACCESS_TOKEN: str = ""
    DROPBOX_REFRESH_TOKEN: str = ""
    DROPBOX_TOKEN_EXPIRES_AT: str = ""
    
    # File Upload Settings
    ALLOWED_IMAGE_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    
    # Redis Configuration for Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Optional: API key for MetalpriceAPI (historical metals prices)
    METALPRICE_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"

settings = Settings()