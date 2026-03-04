from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from backend.services.s3_sync import s3_sync_manager
import os

router = APIRouter()

@router.get("/status")
async def get_s3_status():
    """Returns the current S3 sync status and configuration."""
    return await s3_sync_manager.get_sync_status()

@router.get("/files")
async def list_s3_files():
    """Lists all files currently in the S3 knowledge base."""
    files = await s3_sync_manager.list_s3_files()
    return {"files": files, "count": len(files)}

@router.get("/compare")
async def compare_sync():
    """Compares local files with S3 files (simplified)."""
    s3_files = await s3_sync_manager.list_s3_files()
    local_docs = []
    if os.path.exists("data/uploaded_docs_registry.json"):
        import json
        with open("data/uploaded_docs_registry.json", "r") as f:
            registry = json.load(f)
            local_docs = [d["filename"] for d in registry.get("documents", [])]
            
    s3_filenames = [f["key"].split("/")[-1] for f in s3_files if f["key"].startswith("documents/")]
    
    return {
        "local_docs": local_docs,
        "s3_docs": s3_filenames,
        "synced": all(d in s3_filenames for d in local_docs),
        "missing_in_s3": [d for d in local_docs if d not in s3_filenames]
    }

@router.post("/force-sync")
async def force_sync(background_tasks: BackgroundTasks):
    """Manually triggers a full re-sync of indices to S3."""
    background_tasks.add_task(s3_sync_manager.sync_index_to_s3)
    return {"message": "S3 index synchronization triggered in background"}
