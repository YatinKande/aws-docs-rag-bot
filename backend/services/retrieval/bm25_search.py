from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import pickle
import os
import numpy as np

class BM25Index:
    def __init__(self, index_path: str = "data/indexes/bm25/bm25_index.pkl"):
        self.index_path = index_path
        self.bm25 = None
        self.corpus = []
        self.metadatas = []
        self._load()

    def _load(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["bm25"]
                self.corpus = data["corpus"]
                self.metadatas = data["metadatas"]

    def add_documents(self, documents: List[Dict[str, Any]]):
        new_corpus = [doc["content"].split() for doc in documents]
        new_metadatas = [doc["metadata"] for doc in documents]
        
        self.corpus.extend(new_corpus)
        self.metadatas.extend(new_metadatas)
        
        self.bm25 = BM25Okapi(self.corpus)
        
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "bm25": self.bm25,
                "corpus": self.corpus,
                "metadatas": self.metadatas
            }, f)

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.bm25:
            return []
            
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_n = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for i in top_n:
            if scores[i] > 0:
                results.append({
                    "content": " ".join(self.corpus[i]),
                    "metadata": self.metadatas[i],
                    "score": float(scores[i])
                })
        return results

import numpy as np
