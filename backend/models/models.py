from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
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

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, index=True)
    query = Column(Text)
    response = Column(Text)
    rating = Column(Integer)  # 1 for thumbs up, -1 for thumbs down
    correction = Column(Text, nullable=True) # User's explicit correction
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_info = Column(JSON, nullable=True)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    category = Column(String) # e.g., "style", "technical_focus", "frequent_service"
    preference_value = Column(Text) # e.g., "Detailed CLI examples", "EC2 Cost Optimization"
    weight = Column(Numeric, default=1.0) # Strength of the pattern
    last_updated = Column(DateTime, default=datetime.utcnow)
