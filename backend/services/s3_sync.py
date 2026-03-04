"""
S3 Sync Service
Automatically backs up everything to S3
5 seconds after each document upload.
Organized by service and file type.
"""

import asyncio
import json
import os
import boto3
import numpy as np
from datetime import datetime, timezone
from loguru import logger
from botocore.exceptions import ClientError, NoCredentialsError
from backend.core.config import settings


class S3SyncManager:
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.enabled = bool(self.bucket)
        
        if self.enabled:
            try:
                self.s3 = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION or "us-east-1"
                )
                logger.info(
                    f"S3SyncManager initialized for: "
                    f"s3://{self.bucket}"
                )
            except NoCredentialsError:
                logger.warning(
                    "S3: No AWS credentials found. "
                    "S3 sync disabled."
                )
                self.enabled = False
            except ClientError as e:
                logger.warning(f"S3: Bucket error: {e}")
                self.enabled = False
        else:
            logger.info(
                "S3: No bucket configured. "
                "S3 sync disabled."
            )
        
        self._sync_lock = asyncio.Lock()
        self._pending_syncs = 0

    def _get_s3_key(self, prefix: str, 
                    service: str, 
                    filename: str) -> str:
        """Build organized S3 key path"""
        return f"{prefix}{service}/{filename}"

    async def sync_all_after_upload(
        self,
        filename: str,
        service: str,
        file_path: str,
        chunks: list,
        embeddings: list
    ):
        """
        Main entry point. Called after every upload.
        Waits 5 seconds then syncs everything to S3.
        """
        if not self.enabled:
            return

        logger.info(
            f"S3 sync scheduled for {filename} "
            f"in {settings.S3_SYNC_DELAY_SECONDS}s..."
        )
        
        # Wait before syncing (non-blocking)
        await asyncio.sleep(settings.S3_SYNC_DELAY_SECONDS)
        
        logger.info(f"S3 sync starting (Phase 1: File Specific) for {filename}")
        
        # Run file-specific syncs concurrently
        await asyncio.gather(
            self._upload_original_document(
                filename, service, file_path
            ),
            self._upload_chunks(
                filename, service, chunks
            ),
            self._upload_embeddings(
                filename, service, embeddings
            ),
            self._upload_metadata(
                filename, service, chunks
            ),
            return_exceptions=True
        )
        
        # Phase 2: Shared Index/Registry Sync (Debounced)
        async with self._sync_lock:
            self._pending_syncs += 1
            
        # Wait a bit more to catch other concurrent uploads
        await asyncio.sleep(2)
        
        async with self._sync_lock:
            if self._pending_syncs > 0:
                logger.info(f"S3 sync Phase 2 (Shared Index/Registry) starting. Pending: {self._pending_syncs}")
                await asyncio.gather(
                    self._upload_registry(),
                    self._upload_faiss_index(),
                    return_exceptions=True
                )
                self._pending_syncs = 0
        
        logger.info(
            f"S3 sync complete for {filename} "
            f"→ s3://{self.bucket}"
        )

    async def _upload_original_document(
        self, filename: str, 
        service: str, 
        file_path: str
    ):
        """Upload original PDF to documents/service/"""
        try:
            key = self._get_s3_key(
                settings.S3_DOCUMENTS_PREFIX,
                service,
                filename
            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.upload_file(
                    file_path,
                    self.bucket,
                    key,
                    ExtraArgs={
                        "Metadata": {
                            "service": service,
                            "uploaded": datetime.now(
                                timezone.utc
                            ).isoformat(),
                            "source": "cloud-intelligence-rag"
                        }
                    }
                )
            )
            logger.info(
                f"S3 ✅ Document uploaded: "
                f"s3://{self.bucket}/{key}"
            )
        except Exception as e:
            logger.error(
                f"S3 ❌ Document upload failed "
                f"for {filename}: {e}"
            )

    async def verify_and_cleanup_local(self, file_path: str, service: str, filename: str):
        """Checks if file exists in S3, if so, deletes local copy to save space."""
        if not self.enabled:
            return False
            
        try:
            key = self._get_s3_key(settings.S3_DOCUMENTS_PREFIX, service, filename)
            # Verify existence in S3
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.head_object(Bucket=self.bucket, Key=key)
            )
            
            # If we are here, file exists in S3. 
            # Safe to delete local copy.
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"💾 SPACE SAVED: Deleted local {filename} after S3 verification.")
                return True
        except Exception as e:
            logger.warning(f"S3 Cleanup: Could not verify/delete {filename}: {e}")
            
        return False

    async def download_document(self, filename: str, service: str, target_path: str):
        """Downloads a document from S3 to local storage."""
        if not self.enabled:
            raise Exception("S3 sync is disabled.")
            
        try:
            key = self._get_s3_key(settings.S3_DOCUMENTS_PREFIX, service, filename)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.download_file(self.bucket, key, target_path)
            )
            logger.info(f"S3 ✅ Downloaded {filename} from S3.")
            return target_path
        except Exception as e:
            logger.error(f"S3 ❌ Failed to download {filename}: {e}")
            raise

    async def upload_generic_asset(self, file_path: str, s3_prefix: str):
        """Uploads any file to S3 under a specific prefix."""
        if not self.enabled:
            return False
            
        try:
            filename = os.path.basename(file_path)
            key = f"{s3_prefix}{filename}"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.upload_file(
                    file_path, 
                    self.bucket, 
                    key,
                    ExtraArgs={"ContentType": "application/pdf" if filename.endswith(".pdf") else "application/json"}
                )
            )
            logger.info(f"S3 ✅ Asset uploaded: s3://{self.bucket}/{key}")
            return True
        except Exception as e:
            logger.error(f"S3 ❌ Generic asset upload failed for {file_path}: {e}")
            return False

    async def _upload_chunks(
        self,
        filename: str,
        service: str,
        chunks: list
    ):
        """Upload text chunks as JSON"""
        try:
            chunks_data = []
            for i, chunk in enumerate(chunks):
                chunks_data.append({
                    "chunk_index": i,
                    "text": chunk.page_content 
                            if hasattr(chunk, "page_content") 
                            else str(chunk),
                    "metadata": chunk.metadata 
                                if hasattr(chunk, "metadata") 
                                else {},
                    "char_count": len(
                        chunk.page_content 
                        if hasattr(chunk, "page_content") 
                        else str(chunk)
                    )
                })

            chunks_filename = filename.replace(
                ".pdf", "_chunks.json"
            )
            key = self._get_s3_key(
                settings.S3_CHUNKS_PREFIX,
                service,
                chunks_filename
            )

            chunks_json = json.dumps({
                "filename": filename,
                "service": service,
                "total_chunks": len(chunks_data),
                "created": datetime.now(
                    timezone.utc
                ).isoformat(),
                "chunks": chunks_data
            }, indent=2)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=chunks_json.encode("utf-8"),
                    ContentType="application/json"
                )
            )
            logger.info(
                f"S3 ✅ Chunks uploaded "
                f"({len(chunks_data)} chunks): "
                f"s3://{self.bucket}/{key}"
            )
        except Exception as e:
            logger.error(
                f"S3 ❌ Chunks upload failed "
                f"for {filename}: {e}"
            )

    async def _upload_embeddings(
        self,
        filename: str,
        service: str,
        embeddings: list
    ):
        """Upload raw embedding vectors as .npy file"""
        try:
            if not embeddings:
                logger.warning(
                    f"S3: No embeddings to upload "
                    f"for {filename}"
                )
                return

            import tempfile
            embeddings_array = np.array(embeddings)
            embeddings_filename = filename.replace(
                ".pdf", "_embeddings.npy"
            )
            key = self._get_s3_key(
                settings.S3_EMBEDDINGS_PREFIX,
                service,
                embeddings_filename
            )

            # Save to temp file then upload
            with tempfile.NamedTemporaryFile(
                suffix=".npy", delete=False
            ) as tmp:
                np.save(tmp.name, embeddings_array)
                tmp_path = tmp.name

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.upload_file(
                    tmp_path,
                    self.bucket,
                    key
                )
            )
            os.unlink(tmp_path)

            logger.info(
                f"S3 ✅ Embeddings uploaded "
                f"(shape: {embeddings_array.shape}): "
                f"s3://{self.bucket}/{key}"
            )
        except Exception as e:
            logger.error(
                f"S3 ❌ Embeddings upload failed "
                f"for {filename}: {e}"
            )

    async def _upload_metadata(
        self,
        filename: str,
        service: str,
        chunks: list
    ):
        """Upload document metadata summary"""
        try:
            meta_filename = filename.replace(
                ".pdf", "_meta.json"
            )
            key = self._get_s3_key(
                settings.S3_METADATA_PREFIX,
                service,
                meta_filename
            )

            # Calculate stats
            total_chars = sum(
                len(
                    c.page_content 
                    if hasattr(c, "page_content") 
                    else str(c)
                )
                for c in chunks
            )

            metadata = {
                "filename": filename,
                "service": service,
                "total_chunks": len(chunks),
                "total_characters": total_chars,
                "avg_chunk_size": (
                    total_chars // len(chunks) 
                    if chunks else 0
                ),
                "ingested_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "s3_paths": {
                    "document": (
                        f"s3://{self.bucket}/"
                        f"{settings.S3_DOCUMENTS_PREFIX}"
                        f"{service}/{filename}"
                    ),
                    "chunks": (
                        f"s3://{self.bucket}/"
                        f"{settings.S3_CHUNKS_PREFIX}"
                        f"{service}/"
                        f"{filename.replace('.pdf','_chunks.json')}"
                    ),
                    "embeddings": (
                        f"s3://{self.bucket}/"
                        f"{settings.S3_EMBEDDINGS_PREFIX}"
                        f"{service}/"
                        f"{filename.replace('.pdf','_embeddings.npy')}"
                    )
                }
            }

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=json.dumps(
                        metadata, indent=2
                    ).encode("utf-8"),
                    ContentType="application/json"
                )
            )
            logger.info(
                f"S3 ✅ Metadata uploaded: "
                f"s3://{self.bucket}/{key}"
            )
        except Exception as e:
            logger.error(
                f"S3 ❌ Metadata upload failed "
                f"for {filename}: {e}"
            )

    async def _upload_registry(self):
        """Sync registry JSON to S3"""
        try:
            registry_path = (
                "data/uploaded_docs_registry.json"
            )
            if not os.path.exists(registry_path):
                return

            key = (
                f"{settings.S3_REGISTRY_PREFIX}"
                f"uploaded_docs_registry.json"
            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.upload_file(
                    registry_path,
                    self.bucket,
                    key
                )
            )
            logger.info(
                f"S3 ✅ Registry synced: "
                f"s3://{self.bucket}/{key}"
            )
        except Exception as e:
            logger.error(
                f"S3 ❌ Registry sync failed: {e}"
            )

    async def _upload_faiss_index(self):
        """Sync FAISS index files to S3"""
        try:
            faiss_dir = "data/indexes/faiss"
            if not os.path.exists(faiss_dir):
                return

            for fname in ["index.faiss", "index.pkl"]:
                fpath = os.path.join(faiss_dir, fname)
                if not os.path.exists(fpath):
                    continue

                key = (
                    f"{settings.S3_INDEXES_PREFIX}"
                    f"faiss/{fname}"
                )
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda p=fpath, k=key: (
                        self.s3.upload_file(
                            p, self.bucket, k
                        )
                    )
                )
                logger.info(
                    f"S3 ✅ FAISS index synced: "
                    f"s3://{self.bucket}/{key}"
                )
        except Exception as e:
            logger.error(
                f"S3 ❌ FAISS index sync failed: {e}"
            )

    async def pull_index_from_s3(self):
        """Alias for pull_all_from_s3 to match existing callers"""
        await self.pull_all_from_s3()

    async def sync_index_to_s3(self):
        """Public method to sync vector index to S3"""
        if not self.enabled:
            return
        await self._upload_faiss_index()

    async def pull_registry_from_s3(self):
        """Public method to pull the document registry from S3."""
        if not self.enabled:
            return
        await self._pull_registry()

    async def pull_all_from_s3(self):
        """
        On startup: pull everything from S3 
        so new users have instant access.
        Downloads indexes and registry only
        (not all PDFs to save disk space).
        """
        if not self.enabled:
            return

        logger.info(
            "S3: Pulling latest indexes "
            "and registry from S3..."
        )

        await asyncio.gather(
            self._pull_faiss_index(),
            self._pull_registry(),
            return_exceptions=True
        )

        logger.info("S3: Pull complete.")

    async def _pull_faiss_index(self):
        """Download FAISS index from S3 on startup"""
        try:
            os.makedirs(
                "data/indexes/faiss", exist_ok=True
            )
            for fname in ["index.faiss", "index.pkl"]:
                key = (
                    f"{settings.S3_INDEXES_PREFIX}"
                    f"faiss/{fname}"
                )
                local_path = (
                    f"data/indexes/faiss/{fname}"
                )
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda k=key, p=local_path: (
                        self.s3.download_file(
                            self.bucket, k, p
                        )
                    )
                )
                logger.info(
                    f"S3: Downloaded {fname} from S3"
                )
        except Exception as e:
            logger.warning(
                f"S3: Could not pull FAISS index: {e}"
            )

    async def _pull_registry(self):
        """Download registry from S3 on startup"""
        try:
            key = (
                f"{settings.S3_REGISTRY_PREFIX}"
                f"uploaded_docs_registry.json"
            )
            local_path = (
                "data/uploaded_docs_registry.json"
            )
            os.makedirs("data", exist_ok=True)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3.download_file(
                    self.bucket, key, local_path
                )
            )
            logger.info("S3: Registry pulled from S3")
        except Exception as e:
            logger.warning(
                f"S3: Could not pull registry: {e}"
            )

    async def get_bucket_summary(self) -> dict:
        """Return summary of everything in S3"""
        if not self.enabled:
            return {"enabled": False}

        try:
            paginator = self.s3.get_paginator(
                "list_objects_v2"
            )
            
            summary = {
                "enabled": True,
                "bucket": self.bucket,
                "documents": [],
                "total_files": 0,
                "total_size_mb": 0
            }

            loop = asyncio.get_event_loop()
            pages = await loop.run_in_executor(
                None,
                lambda: list(
                    paginator.paginate(Bucket=self.bucket)
                )
            )

            for page in pages:
                for obj in page.get("Contents", []):
                    summary["total_files"] += 1
                    summary["total_size_mb"] += (
                        obj["Size"] / (1024 * 1024)
                    )
                    if obj["Key"].startswith(
                        settings.S3_DOCUMENTS_PREFIX
                    ):
                        summary["documents"].append(
                            obj["Key"]
                        )

            summary["total_size_mb"] = round(
                summary["total_size_mb"], 2
            )
            return summary

        except Exception as e:
            logger.error(
                f"S3: Failed to get summary: {e}"
            )
            return {"enabled": True, "error": str(e)}


# Global singleton
s3_sync_manager = S3SyncManager()
