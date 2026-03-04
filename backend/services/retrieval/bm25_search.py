"""
BM25 Search Service
- Identifies and fixes syntax and logical bugs
- Implements robust error handling with loguru
- Replaces prints with logging
"""
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
import pickle
import os
import re
from loguru import logger
from backend.core.config import settings

class BM25Index:
    def __init__(self, index_path: Optional[str] = None):
        self.index_path = index_path or os.path.join("data", "indexes", "bm25", "bm25_index.pkl")
        self.bm25 = None
        self.corpus = []
        self.original_corpus = [] 
        self.metadatas = []
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        self._load()

    def _load(self):
        """Loads the BM25 index from disk."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.bm25 = data.get("bm25")
                    self.corpus = data.get("corpus", [])
                    self.original_corpus = data.get("original_corpus", [])
                    self.metadatas = data.get("metadatas", [])
                logger.info(f"BM25 index loaded from {self.index_path}")
            except Exception as e:
                logger.error(f"Failed to load BM25 index from {self.index_path}: {e}")

    def _tokenize(self, text: str) -> List[str]:
        """Robust tokenization for better matching."""
        try:
            # Remove punctuation and split by whitespace
            text = re.sub(r'[^\w\s]', ' ', text.lower())
            return text.split()
        except Exception as e:
            logger.error(f"Tokenization error: {e}")
            return []

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Adds documents to the BM25 index."""
        try:
            new_corpus = [self._tokenize(doc["content"]) for doc in documents]
            new_original_corpus = [doc["content"] for doc in documents]
            new_metadatas = [doc["metadata"] for doc in documents]
            
            self.corpus.extend(new_corpus)
            self.original_corpus.extend(new_original_corpus)
            self.metadatas.extend(new_metadatas)
            
            if self.corpus:
                self.bm25 = BM25Okapi(self.corpus)
            
            with open(self.index_path, "wb") as f:
                pickle.dump({
                    "bm25": self.bm25,
                    "corpus": self.corpus,
                    "original_corpus": self.original_corpus,
                    "metadatas": self.metadatas
                }, f)
            logger.info(f"Added {len(documents)} documents to BM25 index.")
        except Exception as e:
            logger.error(f"Failed to add documents to BM25: {e}")

    def search(self, query: str, top_k: int = 20, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Searches the BM25 index with optional filtering."""
        try:
            if not self.bm25 or not self.corpus:
                return []
                
            tokenized_query = self._tokenize(query)
            if not tokenized_query:
                return []

            scores = self.bm25.get_scores(tokenized_query)
            
            # Apply filter if provided
            candidate_indices = []
            for i, meta in enumerate(self.metadatas):
                if filter:
                    match = True
                    for key, value in filter.items():
                        actual_meta = meta.get(key)
                        if isinstance(value, list):
                            if actual_meta not in value:
                                match = False
                                break
                        elif actual_meta != value:
                            match = False
                            break
                    if not match:
                        continue
                
                if scores[i] > 0:
                    candidate_indices.append(i)
            
            if not candidate_indices:
                return []
                
            # Sort only among candidates
            candidate_scores = [(i, scores[i]) for i in candidate_indices]
            candidate_scores.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for i, score in candidate_scores[:top_k]:
                content = self.original_corpus[i] if i < len(self.original_corpus) else " ".join(self.corpus[i])
                results.append({
                    "content": content,
                    "metadata": self.metadatas[i],
                    "score": float(score)
                })
            return results
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    async def delete_documents(self, filter_dict: Dict[str, Any]):
        """Delete documents from BM25 index based on metadata."""
        try:
            indices_to_delete = []
            for i, meta in enumerate(self.metadatas):
                match = True
                for key, value in filter_dict.items():
                    if meta.get(key) != value:
                        match = False
                        break
                if match:
                    indices_to_delete.append(i)
            
            if indices_to_delete:
                # Delete in reverse order to maintain indices
                for i in sorted(indices_to_delete, reverse=True):
                    if i < len(self.corpus): self.corpus.pop(i)
                    if i < len(self.original_corpus): self.original_corpus.pop(i)
                    if i < len(self.metadatas): self.metadatas.pop(i)
                
                # Rebuild index
                if self.corpus:
                    self.bm25 = BM25Okapi(self.corpus)
                else:
                    self.bm25 = None
                
                # Save
                with open(self.index_path, "wb") as f:
                    pickle.dump({
                        "bm25": self.bm25,
                        "corpus": self.corpus,
                        "original_corpus": self.original_corpus,
                        "metadatas": self.metadatas
                    }, f)
                logger.info(f"Deleted {len(indices_to_delete)} documents from BM25 matching {filter_dict}")
        except Exception as e:
            logger.error(f"Failed to delete documents from BM25: {e}")
