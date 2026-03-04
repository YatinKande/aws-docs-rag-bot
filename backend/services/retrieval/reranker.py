"""
Reranker Service
- Identifies and fixes syntax and logical bugs
- Implements robust error handling with loguru
- Ensures CPU-bound reranking is run in a separate thread
"""
from typing import List, Dict, Any, Optional
import asyncio
from sentence_transformers import CrossEncoder
from flashrank import Ranker, RerankRequest
from loguru import logger
from backend.core.config import settings

class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self.cross_encoder = None
        self.flash_ranker = None
        
        # Lazy load models to avoid heavy init on every import
        self._init_models()

    def _init_models(self):
        """Initializes reranking models with proper error handling."""
        # Stage 2: FlashRank (Very fast, lightweight)
        try:
            # Check if cache dir exists
            os.makedirs("data/models", exist_ok=True)
            self.flash_ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="data/models")
            logger.info("FlashRank ranker initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize FlashRank: {e}")

        # Stage 3: BGE Cross-Encoder (Most accurate, heavier)
        try:
            self.cross_encoder = CrossEncoder(self.model_name, device="cpu") 
            logger.info(f"BGE Cross-Encoder {self.model_name} initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize BGE Cross-Encoder: {e}")

    async def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Reranks candidates using multiple stages: FlashRank then BGE Cross-Encoder."""
        if not candidates:
            return []
            
        try:
            # 1. FlashRank Phase (Fast pruning) - Run in executor
            if self.flash_ranker:
                candidates = await self._run_flashrank(query, candidates)

            # 2. BGE Cross-Encoder Phase (Precision reranking) - Run in executor
            if self.cross_encoder and candidates:
                candidates = await self._run_cross_encoder(query, candidates)
            else:
                # Basic fallback if models fail
                candidates = self._simple_rerank_fallback(query, candidates)

            return candidates[:top_k]
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return candidates[:top_k]

    async def _run_flashrank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Wraps FlashRank blocking call in an executor."""
        def _sync_flash():
            flash_docs = [{"id": str(i), "text": c["content"], "meta": c.get("metadata", {})} for i, c in enumerate(candidates)]
            rank_request = RerankRequest(query=query, passages=flash_docs)
            flash_results = self.flash_ranker.rerank(rank_request)
            return [
                {"content": res["text"], "metadata": res["meta"], "flash_score": float(res["score"])}
                for res in flash_results
            ]
        
        try:
            return await asyncio.get_event_loop().run_in_executor(None, _sync_flash)
        except Exception as e:
            logger.warning(f"FlashRank execution failed: {e}")
            return candidates

    async def _run_cross_encoder(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Wraps Cross-Encoder prediction in an executor."""
        def _sync_cross():
            pairs = [(query, c["content"]) for c in candidates]
            scores = self.cross_encoder.predict(pairs)
            for i, score in enumerate(scores):
                candidates[i]["rerank_score"] = float(score)
            return sorted(candidates, key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        try:
            return await asyncio.get_event_loop().run_in_executor(None, _sync_cross)
        except Exception as e:
            logger.warning(f"Cross-Encoder execution failed: {e}")
            return candidates

    def _simple_rerank_fallback(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple keyword-based boost as a final fallback."""
        query_lower = query.lower()
        for c in candidates:
            content_lower = c["content"].lower()
            # Start with flash score or generic 0.5
            score = c.get("flash_score", 0.5)
            # Boost if terms match
            if any(term in content_lower for term in query_lower.split()):
                score += 0.2
            c["rerank_score"] = score
        return sorted(candidates, key=lambda x: x.get("rerank_score", 0), reverse=True)

import os # Required for makedirs
