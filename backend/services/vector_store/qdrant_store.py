from typing import List, Dict, Any
from langchain_qdrant import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from backend.services.vector_store.base import VectorStoreBase
from backend.core.config import settings
from qdrant_client import QdrantClient

class QdrantStore(VectorStoreBase):
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.collection_name = "rag_docs"
        # Using local storage in a folder
        self.client = QdrantClient(path="qdrant_db")
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
            distance_strategy="COSINE"
        )

    async def add_documents(self, documents: List[Dict[str, Any]]):
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
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
