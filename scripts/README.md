# Scripts Directory

This directory contains utility scripts for running and managing the AWS RAG Bot application.

## Categorized Scripts

### 🛠️ Maintenance (`scripts/maintenance/`)
Scripts for keeping the database and vector index healthy.
- `sync_existing.py`: Synchronizes local documents with the vector store.
- `reingest_docs.py`: Force re-processing of documents.
- `fix_db_keys.py`: Corrects metadata keys in the SQL database.
- `scrape_2026_updates.py`: Pulls latest AWS documentation.

### 🔍 Debug & Diagnostics (`scripts/debug/`)
Tools to inspect indices and diagnose issues.
- `inspect_faiss.py`: Dumps metadata from the FAISS index.
- `check_signatures.py`: Verifies file hashes for change detection.
- `audit_backend.py`: Checks for consistency between DB and S3.

### 🧰 Tools & Utilities (`scripts/tools/`)
General purpose data tools.
- `universal_extractor.py`: Extracts text from various formats.
- `process_training_data.py`: Prepares datasets for tuning.

### 🧪 Tests & Verification (`tests/scripts/`)
Functional test scripts to verify system components.
- `test_connections.py`: Verifies AWS and Database connectivity.
- `test_retrieval.py`: Tests the RAG pipeline quality.
- `verify_image_analysis.py`: Tests vision/OCR capabilities.

---

## Core Entry Points

### `run_backend.py`
Starts the FastAPI backend server with hot reload enabled.
```bash
python scripts/run_backend.py
```

### `start.sh`
Complete application startup script that handles both backend and frontend.
```bash
bash scripts/start.sh
```
