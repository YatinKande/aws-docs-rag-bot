import asyncio
import sys
import os
from loguru import logger

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.services.retrieval.advanced_retrieval import AdvancedRetrieval
from backend.services.retrieval.hybrid_search import HybridSearch

async def test_all_connections():
    print("🔍 Testing Vector Database Connections...")
    hs = HybridSearch()
    
    dbs = ["faiss", "chroma", "lancedb", "milvus", "qdrant"]
    results = {}

    for db in dbs:
        print(f"\n📡 Testing {db.upper()}...")
        try:
            store = hs._get_store(db)
            if not store:
                print(f"❌ {db.upper()}: Initialization failed (returned None).")
                results[db] = "FAILED"
                continue
            
            # Simple health check by searching with a dummy query
            # We don't care about results, just that it doesn't crash
            try:
                await store.search("ping", top_k=1)
                print(f"✅ {db.upper()}: Connected and responsive.")
                results[db] = "OK"
            except Exception as se:
                print(f"❌ {db.upper()}: Search failed: {se}")
                results[db] = "SEARCH_FAILED"
                
        except Exception as e:
            print(f"❌ {db.upper()}: Connection failed: {e}")
            results[db] = "CONNECTION_FAILED"

    print("\n" + "="*30)
    print("📊 CONNECTION SUMMARY")
    print("="*30)
    for db, status in results.items():
        print(f"{db.ljust(10)}: {status}")
    print("="*30)

if __name__ == "__main__":
    asyncio.run(test_all_connections())
