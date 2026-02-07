import os
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from backend.services.vector_store.base import VectorStoreBase
from backend.core.config import settings

class ChromaStore(VectorStoreBase):
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.persist_directory = "data/indexes/chroma"
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="rag_docs",
            collection_metadata={"hnsw:space": "cosine"}
        )

    async def add_documents(self, documents: List[Dict[str, Any]]):
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        # Chroma handles persistence automatically in newer versions
        self.vector_store.add_texts(texts, metadatas=metadatas)

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        docs = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            })
        return results
