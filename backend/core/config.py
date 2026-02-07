from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Cloud-Aware RAG Bot"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security
    # IMPORTANT: Generate this using SecretManager.generate_master_key()
    MASTER_ENCRYPTION_KEY: str = "your-fallback-key-for-dev-only" 
    SECRET_KEY: str = "supersecretjwtkey" # For JWT tokens
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/database/sql_app.db"
    
    # Vector Store
    VECTOR_DB_TYPE: str = "faiss" # faiss, chroma, pinecone, etc.
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Cloud Provider Defaults
    AWS_DEFAULT_REGION: str = "us-east-1"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
