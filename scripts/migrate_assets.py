import asyncio
import os
import shutil
import sys
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.s3_sync import s3_sync_manager

# Configuration
DOCS_S3_PREFIX = "documentation/"
DATA_S3_PREFIX = "analysis_results/"
LOG_DIR = "logs/"

async def migrate():
    if not s3_sync_manager.enabled:
        print("❌ S3 sync is not enabled in settings.")
        return

    # 1. Handle PDFs in root
    pdfs = [f for f in os.listdir(".") if f.endswith(".pdf") and os.path.isfile(f)]
    for pdf in pdfs:
        print(f"📦 Migrating PDF: {pdf} ...")
        success = await s3_sync_manager.upload_generic_asset(pdf, DOCS_S3_PREFIX)
        if success:
            # Verify and delete
            # (Note: we use a simpler verification here)
            print(f"✅ {pdf} moved to S3. Deleting locally...")
            os.remove(pdf)
    
    # 2. Handle JSON results in root
    jsons = [f for f in os.listdir(".") if f.endswith(".json") and "res" in f.lower() and os.path.isfile(f)]
    for js in jsons:
        print(f"📊 Migrating JSON result: {js} ...")
        success = await s3_sync_manager.upload_generic_asset(js, DATA_S3_PREFIX)
        if success:
            print(f"✅ {js} moved to S3. Deleting locally...")
            os.remove(js)

    # 3. Handle loose logs in root
    logs = [f for f in os.listdir(".") if f.endswith(".log") and os.path.isfile(f)]
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    for log_file in logs:
        if log_file == "backend.log":
             # Skip active backend log if possible, or just move anyway
             pass
        print(f"📝 Moving log to {LOG_DIR}: {log_file} ...")
        target = os.path.join(LOG_DIR, log_file)
        # Handle collision
        if os.path.exists(target):
             target = target.replace(".log", f"_{int(asyncio.get_event_loop().time())}.log")
        shutil.move(log_file, target)

    print("\n✨ Migration and Cleanup Complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
