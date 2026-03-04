from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Cloud-Aware RAG Bot"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security
    MASTER_ENCRYPTION_KEY: str
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/database/sql_app.db"
    
    # Vector Store
    VECTOR_DB_TYPE: str = "faiss" # faiss, chroma, pinecone, etc.
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Ollama Models
    OLLAMA_TEXT_MODEL: str = "llama3.2"
    OLLAMA_VISION_MODEL: str = "llava"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # RAG Upgrade Settings
    ENABLE_LLM_JUDGE: bool = True
    RETRIEVAL_CONFIDENCE_THRESHOLD: float = 0.4
    
    # Cloud Provider Defaults
    ENABLE_CLOUD_PROVIDERS: bool = False # Set to True to enable live AWS/GCP/Azure queries
    AWS_DEFAULT_REGION: str = "us-east-1"
    
    # S3 Sync Settings
    S3_KNOWLEDGE_BASE_BUCKET: Optional[str] = None
    S3_INDEX_PREFIX: str = "shared-index/"
    
    # AWS Credentials for S3 Sync (Fallback)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # S3 Backup System
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "us-east-1"
    S3_DOCUMENTS_PREFIX: str = "documents/"
    S3_CHUNKS_PREFIX: str = "chunks/"
    S3_EMBEDDINGS_PREFIX: str = "embeddings/"
    S3_INDEXES_PREFIX: str = "indexes/"
    S3_REGISTRY_PREFIX: str = "registry/"
    S3_METADATA_PREFIX: str = "metadata/"
    S3_SYNC_DELAY_SECONDS: int = 5
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
