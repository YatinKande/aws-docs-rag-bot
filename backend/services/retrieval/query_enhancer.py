from typing import List, Dict, Any
import os
from backend.services.llm_service import LLMService

class QueryEnhancer:
    def __init__(self):
        self.llm_service = LLMService()

    async def expand_query(self, query: str) -> List[str]:
        """Generates query variations for broader retrieval using LLM."""
        if not self.llm_service.llm:
            # Fallback to simple logic if LLM not available
            variations = [query]
            query_l = query.lower()
            if "aws" in query_l: variations.append(query.replace("aws", "amazon web services"))
            return list(set(variations))

        prompt = f"""Generate 3 variations of the following search query to improve document retrieval. 
        Output only the variations, one per line.
        Query: {query}"""
        
        try:
            from langchain.schema import HumanMessage
            response = await self.llm_service.llm.ainvoke([HumanMessage(content=prompt)])
            variations = [line.strip() for line in response.content.split("\n") if line.strip()]
            variations.append(query)
            return list(set(variations))
        except:
            return [query]

    async def generate_hypothetical_answer(self, query: str) -> str:
        """Hypothetical Document Embeddings (HyDE) logic."""
        # Generates a fake answer to use for semantic search
        return f"This is a hypothetical answer to: {query}"
