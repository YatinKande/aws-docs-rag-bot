"""
API Keys API Router
- Manages encryption and storage of cloud credentials
- Implements robust error handling and loguru logging
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
from loguru import logger

from backend.models.database import get_db
from backend.models.models import APIKey
from backend.api.schemas import APIKeyCreate, APIKeyResponse
from backend.core.security import secret_manager

router = APIRouter()

@router.post("/", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_in: APIKeyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Encrypts and stores a new cloud provider API key."""
    try:
        # Encrypt credentials
        encrypted_creds = secret_manager.encrypt(json.dumps(api_key_in.credentials))
        
        new_key = APIKey(
            user_id="default-user",  # Placeholder until Auth is implemented
            provider=api_key_in.provider,
            nickname=api_key_in.nickname,
            encrypted_credentials=encrypted_creds,
            status="active"
        )
        
        db.add(new_key)
        await db.commit()
        await db.refresh(new_key)
        logger.info(f"Created new {api_key_in.provider} API key: {api_key_in.nickname}")
        return new_key
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to store API credentials.")

@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    """Lists all registered API keys for the current user."""
    try:
        result = await db.execute(select(APIKey).where(APIKey.user_id == "default-user"))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve API keys.")

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes an API key."""
    try:
        result = await db.execute(select(APIKey).where(APIKey.id == key_id))
        key = result.scalar_one_or_none()
        if not key:
            raise HTTPException(status_code=404, detail="API Key not found")
        
        await db.delete(key)
        await db.commit()
        logger.info(f"Deleted API key: {key_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key {key_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete API key.")
