from pydantic_settings import BaseSettings
from typing import List, Union
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "PrepSphere"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/prepsphere"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]
    
    # Clerk
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    
    # File upload
    UPLOAD_FOLDER: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Cloudflare R2 (S3-compatible)
    R2_ENDPOINT: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_BASE_URL: str = ""  # e.g., https://cdn.example.com or https://<bucket>.<accountid>.r2.cloudflarestorage.com
    
    # SMTP for email notifications
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    # Resend API fallback
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = ""
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # <-- ADD THIS LINE

settings = Settings()
