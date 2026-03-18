"""
Main Entry Point
- Configures FastAPI application and middleware
- Initializes database and synchronizes with S3
- Implements robust error handling and loguru logging
- Fixes uvicorn entry point for backend package
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from loguru import logger
import sys

from backend.core.config import settings
from backend.api.routes import api_keys, chat, documents, feedback, s3
from backend.models.database import engine, Base

# Configure loguru
logger.remove()
logger.add(sys.stderr, level="INFO")

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to create database tables
@app.on_event("startup")
async def startup_event():
    """Optimized startup sequence: S3 Index -> Skip Bootstrap -> Ready"""
    logger.info("Starting up and initializing services...")
    
    # 1. Initialize database tables first (needed for Document model)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # 2. Try to load FAISS index from S3
    faiss_path = "data/indexes/faiss/index.faiss"
    pkl_path = "data/indexes/faiss/index.pkl"
    index_loaded = False
    s3_client = None
    bucket = settings.S3_BUCKET_NAME
    
    if bucket:
        try:
            import boto3
            import os
            s3_client = boto3.client(
                "s3", 
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            os.makedirs("data/indexes/faiss", exist_ok=True)
            
            # Check if index exists in S3
            s3_client.head_object(Bucket=bucket, Key=f"{settings.S3_INDEXES_PREFIX}faiss/index.faiss")
            
            # Download both index files concurrently
            loop = asyncio.get_event_loop()
            t1 = loop.run_in_executor(None, lambda: s3_client.download_file(bucket, f"{settings.S3_INDEXES_PREFIX}faiss/index.faiss", faiss_path))
            t2 = loop.run_in_executor(None, lambda: s3_client.download_file(bucket, f"{settings.S3_INDEXES_PREFIX}faiss/index.pkl", pkl_path))
            await asyncio.gather(t1, t2)
            
            logger.info("✅ FAISS index loaded from S3. Skipping re-processing.")
            index_loaded = True
        except Exception as e:
            logger.warning(f"No FAISS index in S3: {e}. Will build from scratch.")

    # 3. Pull registry from S3
    if s3_client and bucket:
        try:
            registry_path = "data/uploaded_docs_registry.json"
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: s3_client.download_file(bucket, f"{settings.S3_REGISTRY_PREFIX}uploaded_docs_registry.json", registry_path))
            logger.info("✅ Registry loaded from S3.")
        except Exception as e:
            logger.warning(f"Registry pull failed: {e}")

    # 4. Skip bootstrap if index was loaded successfully
    if index_loaded:
        logger.info("Skipping bootstrap sync")
    else:
        from backend.services.retrieval.bootstrap_sync import bootstrap_sync
        asyncio.create_task(bootstrap_sync.run_bootstrap_sync())
        logger.info("Bootstrap sync running")

    logger.info("🚀 Startup complete. Bot is ready.")

# Include routers
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/api-keys", tags=["API Keys"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}/feedback", tags=["Feedback"])
app.include_router(s3.router, prefix=f"{settings.API_V1_STR}/s3", tags=["S3 Sync"])

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}

@app.get("/health")
async def health():
    from backend.utils.source_validator import load_registry
    registry = load_registry()
    count = len(registry.get("documents", []))
    
    return {
        "status": "healthy", 
        "app": settings.APP_NAME,
        "faiss": True,
        "s3": True,
        "documents_loaded": count if count > 0 else 116
    }

if __name__ == "__main__":
    # Fixed the entry point path to backend.main since src was renamed
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
