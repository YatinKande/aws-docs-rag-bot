# AWS RAG Bot - Folder Structure

This document describes the organization of the AWS RAG Bot codebase.

## Root Directory Structure

```
aws-rag-bot/
├── backend/              # Python FastAPI backend application
├── frontend/             # React TypeScript frontend application
├── data/                 # All data files and indexes
├── logs/                 # Application logs
├── scripts/              # Utility scripts
├── tests/                # Test files
├── docker/               # Docker configuration files
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # Main project README
```

## Backend Directory (`backend/`)

The backend contains all Python code for the FastAPI application:

```
backend/
├── api/                  # API layer
│   ├── routes/          # API route handlers
│   │   ├── api_keys.py  # API key management endpoints
│   │   ├── chat.py      # Chat endpoints
│   │   └── documents.py # Document upload/management endpoints
│   └── schemas.py       # Pydantic schemas for request/response
├── core/                # Core application configuration
│   ├── config.py        # Application settings
│   └── security.py      # Security utilities (encryption, secrets)
├── models/              # Database models
│   ├── database.py      # Database connection and session management
│   └── models.py        # SQLAlchemy ORM models
├── services/            # Business logic layer
│   ├── cloud_providers/ # Cloud provider integrations
│   │   ├── aws/         # AWS-specific handlers (S3, EC2, Lambda, etc.)
│   │   ├── azure/       # Azure client
│   │   ├── gcp/         # GCP client
│   │   ├── base.py      # Base cloud provider interface
│   │   └── factory.py   # Cloud provider factory
│   ├── retrieval/       # RAG retrieval components
│   │   ├── advanced_retrieval.py  # Advanced retrieval orchestration
│   │   ├── bm25_search.py         # BM25 keyword search
│   │   ├── hybrid_search.py       # Hybrid semantic + keyword search
│   │   ├── query_enhancer.py      # Query enhancement with LLM
│   │   ├── reranker.py            # Result reranking
│   │   └── semantic_search.py     # Main retrieval service
│   ├── vector_store/    # Vector database implementations
│   │   ├── base.py      # Base vector store interface
│   │   ├── faiss_store.py   # FAISS implementation
│   │   ├── chroma_store.py  # ChromaDB implementation
│   │   ├── lancedb_store.py # LanceDB implementation
│   │   ├── milvus_store.py  # Milvus implementation
│   │   └── qdrant_store.py  # Qdrant implementation
│   ├── api_key_manager.py   # API key encryption/decryption
│   ├── document_processor.py # Document parsing and chunking
│   ├── llm_service.py       # LLM integration (Ollama)
│   └── router.py            # Query routing logic
├── utils/               # Utility functions
│   ├── cache.py         # Caching utilities
│   └── chunking.py      # Text chunking strategies
└── main.py              # FastAPI application entry point
```

## Frontend Directory (`frontend/`)

The frontend contains the React TypeScript application:

```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── Chat/        # Chat interface components
│   │   ├── Evidence/    # Evidence panel components
│   │   ├── KnowledgeBase/ # Knowledge base management
│   │   └── Settings/    # Settings and API connections
│   ├── services/        # API client services
│   ├── types/           # TypeScript type definitions
│   ├── hooks/           # Custom React hooks
│   ├── utils/           # Utility functions
│   ├── App.tsx          # Main application component
│   └── main.tsx         # Application entry point
├── public/              # Static assets
└── package.json         # Node.js dependencies
```

## Data Directory (`data/`)

All application data is stored here:

```
data/
├── indexes/             # Vector and search indexes
│   ├── faiss/          # FAISS vector store files
│   ├── chroma/         # ChromaDB files
│   └── bm25/           # BM25 index pickle files
├── database/           # SQLite database
│   └── sql_app.db      # Main application database
└── uploads/            # Uploaded files
    └── temp/           # Temporary upload storage
```

> **Note**: The `data/` directory is gitignored and created automatically on first run.

## Logs Directory (`logs/`)

Application logs are stored here:

```
logs/
├── backend.log         # Backend application logs
└── frontend.log        # Frontend development server logs
```

## Scripts Directory (`scripts/`)

Utility scripts for running and managing the application:

```
scripts/
├── run_backend.py      # Backend startup script
└── start.sh            # Full application startup script
```

## Tests Directory (`tests/`)

Test files organized by type:

```
tests/
├── unit/               # Unit tests
│   ├── test_chunking.py
│   └── test_security.py
└── integration/        # Integration tests (future)
```

## Docker Directory (`docker/`)

Docker-related configuration:

```
docker/
├── Dockerfile          # Backend container definition
└── docker-compose.yml  # Multi-service orchestration
```

## Documentation Directory (`docs/`)

Project documentation:

```
docs/
├── README.md           # Documentation index
├── ARCHITECTURE.md     # System architecture overview
├── FOLDER_STRUCTURE.md # This file
├── SETUP.md            # Setup and installation guide
├── API.md              # API documentation
└── DEPLOYMENT.md       # Deployment guide
```

## Key Design Principles

1. **Separation of Concerns**: Backend, frontend, data, and configuration are clearly separated
2. **Modular Architecture**: Services are organized by functionality (retrieval, vector stores, cloud providers)
3. **Data Isolation**: All data files are in a dedicated `data/` directory
4. **Easy Navigation**: Clear folder names and consistent structure
5. **Scalability**: Easy to add new vector stores, cloud providers, or retrieval strategies

## Import Conventions

All Python imports use the `backend.` prefix:

```python
from backend.core.config import settings
from backend.services.llm_service import LLMService
from backend.models.models import Document
```

## Path Conventions

All file paths are relative to the project root:

```python
DATABASE_URL = "sqlite+aiosqlite:///./data/database/sql_app.db"
FAISS_INDEX = "data/indexes/faiss"
CHROMA_DB = "data/indexes/chroma"
BM25_INDEX = "data/indexes/bm25/bm25_index.pkl"
TEMP_UPLOADS = "data/uploads/temp"
```
