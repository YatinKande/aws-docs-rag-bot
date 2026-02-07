from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from backend.models.database import Base

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True) # UUID as string for flexibility
    provider = Column(String)  # "aws", "gcp", "azure", "custom"
    nickname = Column(String)  # User-friendly name
    encrypted_credentials = Column(Text)  # JSON with encrypted keys
    status = Column(String, default="active")  # "active", "invalid", "expired"
    last_validated = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_info = Column(JSON, nullable=True)  # Store account_id, permissions, etc.

class APICallLog(Base):
    __tablename__ = "api_call_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    api_key_id = Column(String, ForeignKey("api_keys.id"))
    provider = Column(String)
    service = Column(String)  # "cost_explorer", "ec2", etc.
    query = Column(Text)
    response_status = Column(String)  # "success", "error", "rate_limited"
    response_time_ms = Column(Numeric)
    cached = Column(Boolean, default=False)
    cost_usd = Column(Numeric(10, 4), nullable=True)  # If applicable
    timestamp = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    filename = Column(String)
    file_type = Column(String)
    source_path = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    status = Column(String, default="pending") # pending, processing, completed, failed
    metadata_info = Column(JSON, nullable=True)
