from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.schemas import ChatRequest, ChatResponse
from backend.services.router import QueryRouter
from backend.models.database import get_db
import uuid

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_query(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    query_router = QueryRouter(db)
    result = await query_router.route(request.query, request.selected_source, request.selected_db)
    
    from backend.services.llm_service import LLMService
    llm_service = LLMService()
    
    context = ""
    source_info = f"Source Type: {result['source_type']}"
    
    if result["source_type"] == "docs":
        context = "\n".join([doc["content"] for doc in result["data"]])
    elif result["source_type"] == "api":
        context = str(result["data"])
        source_info += f", Provider: {result.get('provider')}, Service: {result.get('service')}"
        
    answer = await llm_service.generate_response(request.query, context, source_info)
    
    return ChatResponse(
        answer=answer,
        source_type=result["source_type"],
        source_details=result.get("data", []) if result["source_type"] == "docs" else [],
        conversation_id=request.conversation_id or str(uuid.uuid4())
    )
