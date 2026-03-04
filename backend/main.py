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
    logger.info("Starting up and initializing services...")
    
    try:
        # Pull shared index from S3 before anything else
        from backend.services.s3_sync import s3_sync_manager
        try:
            await s3_sync_manager.pull_index_from_s3()
            logger.info("Shared index pulled from S3.")
        except Exception as s3e:
            logger.warning(f"Failed to pull shared index from S3 (continuing locally): {s3e}")
        
        # Initialize database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
        
        # Register core documents
        from backend.utils.source_validator import register_document
        existing_docs = [
            ("lambda-dg.pdf", "lambda"),
            ("s3-userguide.pdf", "s3"),
            ("ec2-ug.pdf", "ec2"),
        ]
        for filename, service in existing_docs:
            register_document(filename, service)
        logger.info("[STARTUP] Document registry initialized with core documents.")

        # S3 Backup System Startup Pull
        from backend.services.s3_sync import s3_sync_manager
        await s3_sync_manager.pull_all_from_s3()
        logger.info("[STARTUP] S3 synchronization complete.")

        # Bootstrap Synchronization (Sync S3 Docs to Vector DBs)
        from backend.services.retrieval.bootstrap_sync import bootstrap_sync
        # Run bootstrap sync in a separate task so it doesn't block startup completely
        # but we monitor its progress.
        asyncio.create_task(bootstrap_sync.run_bootstrap_sync())
        logger.info("[STARTUP] Bootstrap synchronization task started.")
            
    except Exception as e:
        logger.critical(f"Startup initialization failed: {e}")
        # In a real production app, we might want to exit here
        # sys.exit(1)

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
    return {"status": "healthy", "app": settings.APP_NAME}

if __name__ == "__main__":
    # Fixed the entry point path to backend.main since src was renamed
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
