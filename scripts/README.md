# Scripts Directory

This directory contains utility scripts for running and managing the AWS RAG Bot application.

## Available Scripts

### `run_backend.py`

Starts the FastAPI backend server with hot reload enabled.

**Usage:**
```bash
python scripts/run_backend.py
```

**What it does:**
- Sets up the Python path to include the project root
- Starts Uvicorn server on `0.0.0.0:8000`
- Enables auto-reload for development

**Direct usage:**
```bash
source .venv/bin/activate
python scripts/run_backend.py
```

### `start.sh`

Complete application startup script that handles both backend and frontend.

**Usage:**
```bash
bash scripts/start.sh
```

**What it does:**
1. Cleans up old processes on ports 8000 and 5173
2. Creates `.env` file from template if it doesn't exist
3. Generates encryption keys if needed
4. Installs Python dependencies
5. Installs Node.js dependencies
6. Starts backend server (logs to `logs/backend.log`)
7. Starts frontend dev server (logs to `logs/frontend.log`)
8. Displays access URLs

**Stopping the application:**
Press `Ctrl+C` to stop both services.

## Creating New Scripts

When adding new utility scripts:

1. Place them in this directory
2. Make them executable: `chmod +x scripts/your_script.sh`
3. Add documentation here
4. Use relative paths from project root
5. Handle errors gracefully

## Examples

### Running Backend Only

```bash
python scripts/run_backend.py
```

### Running Full Stack

```bash
bash scripts/start.sh
```

### Custom Script Template

```bash
#!/bin/bash
# scripts/my_script.sh

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Your script logic here
echo "Running from: $PROJECT_ROOT"
```
