# AWS RAG Bot

> **An intelligent chatbot that answers questions from your documents AND your AWS cloud infrastructure**

## What is This Bot?

The AWS RAG Bot is a dual-purpose AI assistant that combines two powerful capabilities:

### 1. 📚 Document Question Answering (RAG)
Upload your documents (PDFs, Word files, text files, etc.) and ask questions about them. The bot uses **Retrieval-Augmented Generation (RAG)** to:
- Extract and chunk your documents intelligently
- Store them in vector databases for semantic search
- Retrieve relevant context when you ask questions
- Generate accurate answers grounded in your documents
- Show you the exact sources and evidence for each answer

**Example Questions:**
- "What are the key findings in the Q4 report?"
- "Summarize the security policies from the uploaded document"
- "What does the manual say about troubleshooting?"

### 2. ☁️ Real-Time AWS Cloud Queries
Connect your AWS account and ask questions about your live cloud infrastructure. The bot:
- Queries your actual AWS resources in real-time (no hallucination!)
- Supports multiple AWS services: S3, EC2, Lambda, RDS, IAM, Cost Explorer
- Interprets natural language questions and routes them to the right AWS APIs
- Provides detailed, accurate information about your cloud setup

**Example Questions:**
- "List all my S3 buckets"
- "What EC2 instances are running in us-east-1?"
- "Show me my AWS costs for this month"
- "Which Lambda functions were deployed recently?"

### 🎯 Why Use This Bot?

- **Unified Interface**: Ask questions about your documents AND cloud infrastructure in one place
- **No Hallucination**: Cloud queries use real AWS API calls, not LLM guesses
- **Privacy-First**: Runs locally with Ollama - your data stays on your machine
- **Intelligent Routing**: Automatically detects whether you're asking about documents or AWS
- **Evidence-Based**: See the sources and reasoning behind every answer
- **Secure**: API keys are encrypted and stored locally

## The Problem This Solves

### Traditional Challenges

**1. Document Knowledge Management**
- Organizations have critical information scattered across PDFs, Word docs, manuals, and reports
- Finding specific information requires manual searching through hundreds of pages
- Knowledge is siloed and not easily accessible to team members
- Traditional search only finds keywords, not semantic meaning

**2. Cloud Infrastructure Visibility**
- DevOps teams need to constantly check AWS console for resource information
- Writing AWS CLI commands requires remembering complex syntax
- Getting simple answers (like "what buckets do I have?") requires multiple clicks or commands
- No unified way to query infrastructure alongside documentation

**3. Fragmented Workflows**
- Teams switch between multiple tools: document readers, AWS console, CLI, wikis
- Context switching reduces productivity
- No single source of truth for both documentation and live infrastructure

## The Solution

This RAG bot provides a **unified conversational interface** that combines:

### 📚 Intelligent Document Search (RAG)
- **Semantic Understanding**: Finds relevant information even if exact keywords don't match
- **Context-Aware**: Retrieves the most relevant document chunks for your question
- **Source Attribution**: Shows you exactly where the answer came from
- **Multi-Format Support**: PDF, DOCX, TXT, CSV, and more

### ☁️ Live Cloud Infrastructure Queries
- **Natural Language to API**: Ask in plain English, get real AWS data
- **Multi-Service Support**: S3, EC2, Lambda, RDS, IAM, Cost Explorer, and more
- **Real-Time Data**: Always up-to-date, no cached or stale information
- **No Hallucination**: Uses actual AWS API responses, not LLM guesses

### 🤖 Smart Query Routing
- **Automatic Detection**: Determines if you're asking about documents or AWS
- **Context Switching**: Seamlessly handles both types of queries in one conversation
- **Intelligent Fallback**: If one source doesn't have the answer, tries the other

## What Makes This Unique

### 1. 🗄️ **Multiple Vector Database Support**
Unlike most RAG systems locked to one database, this bot supports:
- **FAISS**: Fast, in-memory vector search (default)
- **ChromaDB**: Persistent, feature-rich vector store
- **LanceDB**: Modern, columnar vector database
- **Milvus**: Scalable, production-grade vector DB
- **Qdrant**: High-performance vector search engine

**Why this matters**: Choose the right database for your use case - FAISS for speed, ChromaDB for features, Milvus for scale.

### 2. 🔍 **Hybrid Search Architecture**
Combines multiple retrieval strategies:
- **Semantic Search**: Vector similarity using embeddings (finds meaning)
- **Keyword Search**: BM25 algorithm (finds exact terms)
- **Hybrid Fusion**: Combines both for best results
- **Reranking**: Uses cross-encoder to reorder results by relevance

**Why this matters**: Catches both semantic matches ("cost optimization") and exact terms ("AWS billing"), giving you the most comprehensive results.

### 3. 🎯 **Intelligent Multi-Agent Routing**
The bot acts as a **query router** that:
- Analyzes your question using LLM
- Determines intent (document vs. cloud query)
- Routes to the appropriate handler
- Combines results when needed

**Why this matters**: You don't need to specify "search documents" or "query AWS" - the bot figures it out automatically.

### 4. 🔐 **Enterprise-Grade Security**
- **Fernet Encryption**: API keys encrypted at rest using symmetric encryption
- **Local Storage**: All data stays on your machine
- **No External Calls**: LLM runs locally via Ollama
- **Secure Key Management**: Master encryption key stored in environment variables

**Why this matters**: Your AWS credentials and documents never leave your infrastructure.

### 5. 🧩 **Modular & Extensible Architecture**
- **Plugin Vector Stores**: Add new databases by implementing one interface
- **Cloud Provider Factory**: Easily add Azure, GCP, or other providers
- **Service Handlers**: Extend AWS support by adding new service handlers
- **Chunking Strategies**: Multiple text chunking algorithms (fixed, semantic, recursive)

**Why this matters**: Easy to customize and extend for your specific needs.

### 6. 📊 **Advanced RAG Features**
- **Query Enhancement**: LLM improves your question before searching
- **Contextual Chunking**: Smart document splitting that preserves meaning
- **Metadata Filtering**: Filter by document type, date, or custom tags
- **Score Thresholding**: Only returns high-confidence results
- **Evidence Tracking**: Full transparency on what sources were used

**Why this matters**: Production-grade RAG, not just a simple demo.

## Key Features

- 📚 **Advanced RAG Pipeline**: Hybrid search (semantic + keyword), query enhancement, reranking
- ☁️ **Multi-Service AWS Integration**: S3, EC2, Lambda, RDS, IAM, Cost Explorer support
- 🔍 **Smart Query Routing**: Automatically routes questions to documents or AWS
- 🤖 **Local LLM**: Powered by Ollama (Llama 3.2) - no external API calls needed
- 🔐 **Encrypted Credentials**: Your AWS keys are encrypted with Fernet encryption
- 🎨 **Modern UI**: Clean React TypeScript interface with real-time chat
- 📊 **Evidence Panel**: See exactly what sources were used for each answer

## 🚀 Zero-Conf Setup (3 Steps Only)

Get the bot running and synced with the shared knowledge base in minutes.

### 1. Clone the Repo
```bash
git clone <your-repo-url>
cd aws-rag-bot
```

### 2. Configure Environment
Create a `.env` file in the root directory (get the specific values from your Team Lead):
```bash
AWS_ACCESS_KEY_ID=xxxx
AWS_SECRET_ACCESS_KEY=xxxx
AWS_REGION=us-east-1
S3_KNOWLEDGE_BASE_BUCKET=your-bucket-name
S3_INDEX_PREFIX=indexes/
OLLAMA_TEXT_MODEL=llama3.2
OLLAMA_VISION_MODEL=llava
```

### 3. Run the App
```bash
# Install dependencies
pip install -r requirements.txt

# Pull local AI models
ollama pull llama3.2
ollama pull llava

# Start the backend
python -m backend.main
```

> [!IMPORTANT]
> **Zero Re-Uploading Needed**: On startup, the app automatically pulls the shared FAISS index from S3. All 50+ AWS documents are immediately available for querying without any manual ingestion.

## How It Works

### Document Questions (RAG Mode)
1. You upload a document
2. The bot chunks it into smaller pieces
3. Each chunk is converted to a vector (embedding)
4. Vectors are stored in a database (FAISS or ChromaDB)
5. When you ask a question:
   - Your question is converted to a vector
   - Similar document chunks are retrieved
   - The LLM generates an answer using those chunks
   - You see the answer + the source evidence

### AWS Questions (Cloud Mode)
1. You add your AWS credentials
2. When you ask an AWS question:
   - The LLM interprets what you're asking
   - It determines which AWS service to query
   - It makes a real API call to AWS
   - It formats the response in natural language
   - No hallucination - all data is real!

## Project Structure

```
aws-rag-bot/
├── backend/              # FastAPI backend application
├── frontend/             # React TypeScript frontend
├── data/                 # Data files and indexes (created on first run)
├── logs/                 # Application logs
├── scripts/              # Utility scripts (start.sh, run_backend.py)
├── tests/                # Unit and integration tests
├── docker/               # Docker configuration files
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

See [docs/FOLDER_STRUCTURE.md](docs/FOLDER_STRUCTURE.md) for detailed structure documentation.

## Architecture

- **Backend**: FastAPI with async SQLAlchemy
- **Frontend**: React + TypeScript + Vite
- **Vector Stores**: FAISS, ChromaDB (configurable)
- **LLM**: Ollama (local inference)
- **Database**: SQLite (development), PostgreSQL (production)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Development

### Running Tests

```bash
pytest tests/unit/
```

### Running Backend Only

```bash
python scripts/run_backend.py
```

### Running Frontend Only

```bash
cd frontend
npm run dev
```

## Docker Deployment

```bash
cd docker
docker-compose up
```

## Documentation

- [Setup Guide](docs/SETUP.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Folder Structure](docs/FOLDER_STRUCTURE.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Your License Here]

## Acknowledgments

- Built with FastAPI, React, and Ollama
- Uses LangChain for RAG components
- Vector stores: FAISS, ChromaDB
