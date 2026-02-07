#!/bin/bash

# Cloud-Aware RAG Bot Startup Script

echo "🚀 Starting Cloud-Aware RAG Bot..."

# 1. Cleanup existing processes
echo "🧹 Cleaning up old processes..."
lsof -t -i :8000 -i :5173 | xargs kill -9 2>/dev/null

# 2. Setup Backend
echo "🐍 Setting up Backend..."
if [ ! -f ".env" ]; then
    echo "📄 Creating .env from template..."
    cp .env.example .env
    # Generate keys if they don't exist
    KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    sed -i '' "s/MASTER_ENCRYPTION_KEY=/MASTER_ENCRYPTION_KEY=$KEY/" .env
    sed -i '' "s/SECRET_KEY=/SECRET_KEY=$KEY/" .env
fi

# 3. Install Dependencies
echo "📦 Installing Backend dependencies..."
./.venv/bin/pip install -r requirements.txt greenlet > /dev/null

echo "📦 Installing Frontend dependencies..."
cd frontend
npm install > /dev/null
cd ..

# 4. Launch Services
echo "🔥 Launching services..."

# Start Backend
PYTHONPATH=. ./.venv/bin/python3 scripts/run_backend.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Start Frontend
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ Services launched!"
echo "📡 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:5173"
echo "📝 Logs: logs/backend.log, logs/frontend.log"
echo "💡 Press Ctrl+C to stop services."

# Wait for exit
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
