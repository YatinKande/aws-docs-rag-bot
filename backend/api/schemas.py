from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# --- API Key Schemas ---
class APIKeyBase(BaseModel):
    provider: str
    nickname: str
    credentials: Dict[str, str] # Raw credentials before encryption

class APIKeyCreate(APIKeyBase):
    pass

class APIKeyResponse(BaseModel):
    id: str
    user_id: str
    provider: str
    nickname: str
    status: str
    last_validated: Optional[datetime] = None
    last_used: Optional[datetime] = None
    created_at: datetime
    metadata_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- Chat Schemas ---
class ChatMessage(BaseModel):
    role: str # "user", "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    query: str
    selected_source: str = "auto" # Specific API key ID, "docs", "auto", or "hybrid"
    selected_db: str = "faiss" # Target vector database if source is "docs"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    source_type: str # "docs", "api", "hybrid"
    source_details: List[Dict[str, Any]]
    conversation_id: str

# --- Document Schemas ---
class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    upload_date: datetime
    processed: bool
    status: str
    metadata_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
