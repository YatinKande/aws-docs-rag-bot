"""
Chat API Router
- Orchestrates multi-provider routing and RAG pipeline
- Integrates service detection for improved prompt engineering
- Uses loguru for logging
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.schemas import ChatRequest, ChatResponse
from backend.services.router import QueryRouter
from backend.models.database import get_db
from backend.utils.service_detection import detect_service
from backend.utils.source_validator import (
    validate_source, 
    get_valid_sources,
    get_correct_source_for_service
)
from loguru import logger
import uuid

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_query(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Handles user queries by routing between documents (RAG) and Live Cloud APIs."""
    try:
        query_router = QueryRouter(db)
        result = await query_router.route(request.query, request.selected_source, request.selected_db)
        
        from backend.services.llm_service import LLMService
        llm_service = LLMService()
        
        context = ""
        sources = []
        
        # Detect target service for prompt specialization
        primary_service = detect_service(request.query)

        if result["source_type"] == "docs":
            # Extract clean sources and format context
            context_parts = []
            chunks = result.get("data") or result.get("chunks") or result.get("results") or []
            
            for chunk in chunks:
                if isinstance(chunk, dict):
                    src = chunk.get("source") or chunk.get("metadata", {}).get("source", "")
                    content = chunk.get("content", "")
                    chunk_idx = chunk.get("metadata", {}).get("chunk_index", "?")
                elif hasattr(chunk, "metadata"):
                    src = chunk.metadata.get("source", "")
                    content = chunk.page_content if hasattr(chunk, "page_content") else str(chunk)
                    chunk_idx = chunk.metadata.get("chunk_index", "?")
                else:
                    src = ""
                    content = str(chunk)
                    chunk_idx = "?"
                
                if src and src not in sources:
                    sources.append(src)
                
                if content:
                    context_parts.append(f"SOURCE: {src} (Chunk {chunk_idx})\nCONTENT: {content}")
            
            # Validate all sources before passing to LLM
            valid = get_valid_sources()
            validated_sources = []
            for s in sources:
                if any(v.lower() in s.lower() for v in valid):
                    validated_sources.append(s)
            
            if not validated_sources and primary_service:
                validated_sources = [get_correct_source_for_service(primary_service)]
            
            sources = validated_sources
            context = "\n\n".join(context_parts)
            
        elif result["source_type"] == "api":
            context = str(result["data"])
            sources = [f"{result.get('provider', 'AWS').upper()} API: {result.get('service', '').upper()}"]
            
        from backend.services.learning_service import LearningService
        learning_service = LearningService(db)
        user_id = "default_user" 
        insights = await learning_service.get_user_insights(user_id)

        # Generate response using the improved RAG prompt
        answer = await llm_service.generate_response(
            request.query, 
            context, 
            sources,
            service=primary_service,
            learned_insights=insights
        )
        
        logger.info(f"Query processed successfully. Source: {result['source_type']}")
        
        return ChatResponse(
            answer=answer,
            source_type=result["source_type"],
            source_details=result.get("data", []) or result.get("chunks", []) or result.get("results", []),
            conversation_id=request.conversation_id or str(uuid.uuid4().hex)
        )
    except Exception as e:
        logger.error(f"Chat execution failed: {e}")
        return ChatResponse(
            answer=f"I encountered an error processing your request: {str(e)}",
            source_type="error",
            source_details=[],
            conversation_id=request.conversation_id or str(uuid.uuid4().hex)
        )
