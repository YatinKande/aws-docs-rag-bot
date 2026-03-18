"""
Maintenance Script: Local Data Cleanup
Purges temporary and stale files from the data/ directory,
preserving essential databases and indexes.
"""
import os
import shutil
from loguru import logger

# Paths to clean (relative to project root)
TEMP_PATHS = [
    "data/uploads/temp",
    "data/extracted/text",
    "data/extracted/images",
    "data/extracted/tables",
    "data/extracted/raw",
    "data/test_input",
    "data/test_samples"
]

FILES_TO_DELETE = [
    "data/test_upload.zip",
    "data/test_image.png",
    "data/test_image.zip"
]

def cleanup():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logger.info(f"Starting local data cleanup in: {project_root}")
    
    # 1. Clear contents of temp directories
    for path in TEMP_PATHS:
        abs_path = os.path.join(project_root, path)
        if os.path.exists(abs_path):
            count = 0
            for item in os.listdir(abs_path):
                item_path = os.path.join(abs_path, item)
                if item == ".gitkeep":
                    continue
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {item_path}: {e}")
            logger.info(f"Cleared {count} items from {path}")

    # 2. Delete specific stale files
    for file_rel in FILES_TO_DELETE:
        abs_file = os.path.join(project_root, file_rel)
        if os.path.exists(abs_file):
            try:
                os.remove(abs_file)
                logger.info(f"Deleted stale file: {file_rel}")
            except Exception as e:
                logger.error(f"Failed to delete {abs_file}: {e}")

    logger.info("Cleanup complete. Essential indexes and databases preserved.")

if __name__ == "__main__":
    cleanup()
