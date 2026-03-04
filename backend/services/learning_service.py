import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.models.models import Feedback, UserPreference, APICallLog
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class LearningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_patterns(self, user_id: str):
        """
        Analyzes recent user behavior and feedback to distill preferences.
        """
        try:
            # 1. Analyze frequency of services used
            query = select(APICallLog.service).where(APICallLog.user_id == user_id)
            result = await self.db.execute(query)
            services = [row[0] for row in result.all()]
            
            from collections import Counter
            service_counts = Counter(services)
            
            for service, count in service_counts.most_common(3):
                if count >= 3: # Threshold for a pattern
                    await self._update_preference(
                        user_id, 
                        "frequent_service", 
                        f"User often asks about {service.upper()}",
                        weight=float(count) / 10.0
                    )

            # 2. Analyze feedback corrections
            # This would ideally use an LLM to summarize corrections, 
            # but for now we'll store the direct corrections.
            feedback_query = select(Feedback).where(
                Feedback.rating == -1, 
                Feedback.correction != None
            )
            feedback_result = await self.db.execute(feedback_query)
            for feedback in feedback_result.scalars().all():
                # Store specific corrections as patterns or QA pairs
                logger.info(f"Learning from correction: {feedback.correction[:50]}...")
            
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            await self.db.rollback()

    async def _update_preference(self, user_id: str, category: str, value: str, weight: float):
        query = select(UserPreference).where(
            UserPreference.user_id == user_id,
            UserPreference.category == category,
            UserPreference.preference_value == value
        )
        result = await self.db.execute(query)
        pref = result.scalar_one_or_none()
        
        if pref:
            pref.weight = weight
            pref.last_updated = datetime.utcnow()
        else:
            new_pref = UserPreference(
                user_id=user_id,
                category=category,
                preference_value=value,
                weight=weight
            )
            self.db.add(new_pref)

    async def get_user_insights(self, user_id: str) -> str:
        """Retrieves distilled insights as a string for LLM context."""
        query = select(UserPreference).where(UserPreference.user_id == user_id).order_by(UserPreference.weight.desc())
        result = await self.db.execute(query)
        prefs = result.scalars().all()
        
        if not prefs:
            return ""
            
        insights = "LEARNED USER PREFERENCES:\n"
        for p in prefs:
            insights += f"- {p.preference_value}\n"
        return insights
