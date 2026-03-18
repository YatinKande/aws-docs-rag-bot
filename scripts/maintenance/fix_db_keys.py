import asyncio
from backend.models.database import AsyncSessionLocal
from backend.models.models import APIKey
from sqlalchemy import select, delete

async def fix_keys():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(APIKey))
        keys = res.scalars().all()
        print(f"Checking {len(keys)} keys in database...")
        
        # If we have keys, let's just clear them or re-encrypt.
        # Since we've changed the MASTER_ENCRYPTION_KEY, 
        # the old ones are unusable.
        if keys:
            print("Purging unusable keys to stop decryption errors...")
            await db.execute(delete(APIKey))
            await db.commit()
            print("Successfully cleared all API keys. Users will need to re-add them if needed.")
        else:
            print("No keys found in database.")

if __name__ == "__main__":
    asyncio.run(fix_keys())
