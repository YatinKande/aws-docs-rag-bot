# AWS RAG Bot - Setup Guide

This guide will help you set up and run the AWS RAG Bot on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)
- **Ollama**: [Install Ollama](https://ollama.ai/)
- **Git**: [Download Git](https://git-scm.com/downloads)

## Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd aws-rag-bot
```

## Step 2: Backend Setup

### Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Set Up Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Generate a secure encryption key
MASTER_ENCRYPTION_KEY=<generate-using-cryptography.fernet>
SECRET_KEY=<your-secret-key>

# AWS Configuration (optional, can be added via UI)
AWS_DEFAULT_REGION=us-east-1

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
```

To generate a secure encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Step 3: Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## Step 4: Install and Configure Ollama

### Install Ollama

Follow the instructions at [ollama.ai](https://ollama.ai/) to install Ollama for your platform.

### Pull Required Models

```bash
ollama pull llama3.2
# or
ollama pull llama3.1
```

### Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

## Step 5: Run the Application

### Option 1: Use the Startup Script (Recommended)

```bash
bash scripts/start.sh
```

This will:
- Clean up old processes
- Install dependencies
- Start both backend and frontend
- Display access URLs

### Option 2: Run Services Manually

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
python scripts/run_backend.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Step 6: Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Step 7: Configure AWS Credentials (Optional)

1. Open the application at http://localhost:5173
2. Navigate to **Settings** → **API Connections**
3. Add your AWS credentials:
   - Provider: AWS
   - Access Key ID: Your AWS access key
   - Secret Access Key: Your AWS secret key
   - Region: Your preferred region (e.g., us-east-1)

Your credentials are encrypted and stored securely in the local database.

## Troubleshooting

### Backend Won't Start

**Issue**: Import errors or module not found

**Solution**: Ensure you're in the virtual environment and all dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend Won't Start

**Issue**: Module not found or dependency errors

**Solution**: Reinstall dependencies:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Ollama Connection Error

**Issue**: Cannot connect to Ollama

**Solution**: 
1. Verify Ollama is running: `ollama list`
2. Check the Ollama URL in your `.env` file
3. Restart Ollama: `ollama serve`

### Database Errors

**Issue**: Database locked or permission errors

**Solution**: 
1. Stop all running instances
2. Delete the database: `rm data/database/sql_app.db`
3. Restart the application (database will be recreated)

### Port Already in Use

**Issue**: Port 8000 or 5173 already in use

**Solution**: Kill the process using the port:
```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Development Tips

### Running Tests

```bash
pytest tests/unit/ -v
```

### Viewing Logs

```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

### Clearing Data

To reset all data (indexes, database, uploads):
```bash
rm -rf data/indexes/*
rm -rf data/database/*
rm -rf data/uploads/temp/*
```

### Hot Reload

Both backend and frontend support hot reload:
- Backend: Automatically reloads on file changes
- Frontend: Automatically reloads on file changes

## Next Steps

- [Architecture Overview](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Folder Structure](FOLDER_STRUCTURE.md)

## Getting Help

If you encounter issues not covered here, please:
1. Check the logs in `logs/` directory
2. Review the [Architecture documentation](ARCHITECTURE.md)
3. Open an issue on GitHub
