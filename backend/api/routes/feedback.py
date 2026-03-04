"""
Feedback API Router
- Records user feedback and triggers background learning
- Implements robust error handling and loguru logging
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Optional

from backend.models.database import get_db
from backend.models.models import Feedback
from pydantic import BaseModel
from backend.services.learning_service import LearningService

router = APIRouter()

class FeedbackSubmit(BaseModel):
    conversation_id: str
    query: str
    response: str
    rating: int # 1 or -1
    correction: Optional[str] = None
    user_id: Optional[str] = "default_user"

@router.post("/")
async def submit_feedback(data: FeedbackSubmit, db: AsyncSession = Depends(get_db)):
    """Submits user feedback and triggers pattern analysis."""
    try:
        feedback = Feedback(
            conversation_id=data.conversation_id,
            query=data.query,
            response=data.response,
            rating=data.rating,
            correction=data.correction
        )
        db.add(feedback)
        await db.commit()
        
        # Trigger pattern analysis in the background
        try:
            learning_service = LearningService(db)
            await learning_service.analyze_patterns(data.user_id)
        except Exception as le:
            logger.error(f"Pattern analysis failed: {le}")
            # We don't fail the feedback submission if learning fails
        
        logger.info(f"Feedback recorded for conversation {data.conversation_id}")
        return {"status": "success", "message": "Feedback recorded and analyzed"}
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to record feedback.")

@router.get("/insights/{user_id}")
async def get_insights(user_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves learning insights for a specific user."""
    try:
        learning_service = LearningService(db)
        insights = await learning_service.get_user_insights(user_id)
        return {"insights": insights}
    except Exception as e:
        logger.error(f"Failed to retrieve insights for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve insights.")
