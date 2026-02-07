from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json

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
    return new_key

@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.user_id == "default-user"))
    return result.scalars().all()

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    await db.delete(key)
    await db.commit()
    return None
