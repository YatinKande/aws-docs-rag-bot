import os
import faiss
import numpy as np
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from backend.services.vector_store.base import VectorStoreBase
from backend.core.config import settings

class FAISSStore(VectorStoreBase):
    def __init__(self):
        # Default to local HuggingFace embeddings if no OpenAI key
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.index_path = "data/indexes/faiss"
        self.vector_store = None
        self._load_or_create()

    def _load_or_create(self):
        if os.path.exists(self.index_path):
            self.vector_store = FAISS.load_local(
                self.index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True,
                distance_strategy="COSINE"
            )
        else:
            # Create an initial empty index if needed, or wait for documents
            pass

    async def add_documents(self, documents: List[Dict[str, Any]]):
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        if self.vector_store:
            self.vector_store.add_texts(texts, metadatas=metadatas)
        else:
            self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas, distance_strategy="COSINE")
        
        self.vector_store.save_local(self.index_path)

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.vector_store:
            return []
            
        docs = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            })
        return results
