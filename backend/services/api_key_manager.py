from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional
import json

from backend.models.models import APIKey
from backend.core.security import secret_manager

class APIKeyManager:
    @staticmethod
    async def get_decrypted_credentials(db: AsyncSession, api_key_id: str) -> Optional[Dict[str, Any]]:
        """Fetches and decrypts credentials for a specific API key."""
        result = await db.execute(select(APIKey).where(APIKey.id == api_key_id))
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return None
            
        decrypted_json = secret_manager.decrypt(api_key.encrypted_credentials)
        return json.loads(decrypted_json)

    @staticmethod
    async def get_active_keys(db: AsyncSession, user_id: str, provider: Optional[str] = None) -> List[APIKey]:
        """Lists active keys for a user, optionally filtered by provider."""
        query = select(APIKey).where(APIKey.user_id == user_id, APIKey.status == "active")
        if provider:
            query = query.where(APIKey.provider == provider)
        
        result = await db.execute(query)
        return result.scalars().all()
