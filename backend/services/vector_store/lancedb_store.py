from typing import List, Dict, Any
from langchain_community.vectorstores import LanceDB
from langchain_community.embeddings import HuggingFaceEmbeddings
from backend.services.vector_store.base import VectorStoreBase
from backend.core.config import settings
import lancedb

class LanceDBStore(VectorStoreBase):
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.uri = "lancedb_data"
        self.table_name = "rag_docs"
        self.db = lancedb.connect(self.uri)
        
        # LanceDB in LangChain is slightly different in init
        self.vector_store = None

    async def add_documents(self, documents: List[Dict[str, Any]]):
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        if self.vector_store is None:
            self.vector_store = LanceDB.from_texts(
                texts, 
                self.embeddings, 
                connection=self.db,
                table_name=self.table_name,
                metadatas=metadatas,
                distance_metric="cosine"
            )
        else:
            self.vector_store.add_texts(texts, metadatas=metadatas)

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # If no docs added yet, LanceDB might not have the table
        if self.vector_store is None:
            try:
                self.vector_store = LanceDB(
                    connection=self.db,
                    embedding=self.embeddings,
                    table_name=self.table_name
                )
            except:
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
