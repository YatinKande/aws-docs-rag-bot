import asyncio
import os
import sys
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.s3_sync import s3_sync_manager
from backend.utils.service_detection import get_service_from_filename

async def sync_existing():
    if not s3_sync_manager.enabled:
        print("❌ S3 sync is not enabled in settings.")
        return

    temp_dir = "data/uploads/temp"
    if not os.path.exists(temp_dir):
        print(f"❌ Temp directory {temp_dir} does not exist.")
        return

    files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f)) and f.endswith(".pdf")]
    print(f"🔍 Found {len(files)} existing PDFs to sync.")

    for filename in files:
        file_path = os.path.join(temp_dir, filename)
        # Extract original name (it has a hex prefix in some cases)
        # 1fadb138_rds-ug.pdf -> rds-ug.pdf
        original_name = filename
        if "_" in filename and len(filename.split("_")[0]) == 8:
            original_name = "_".join(filename.split("_")[1:])
            
        service = get_service_from_filename(original_name)
        print(f"📤 Syncing {filename} (Service: {service})...")
        
        try:
            # We skip chunks/embeddings sync for old files unless we have them.
            # But we definitely want the document back up.
            await s3_sync_manager._upload_original_document(filename, service, file_path)
            
            # Verify and Cleanup
            success = await s3_sync_manager.verify_and_cleanup_local(file_path, service, filename)
            if success:
                print(f"✅ {filename} synced and deleted from local.")
            else:
                print(f"⚠️ {filename} synced but local deletion failed (check permissions).")
        except Exception as e:
            print(f"❌ Failed to sync {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(sync_existing())
