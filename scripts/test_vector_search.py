import asyncio
import os
import sys

# Ensure the root directory is in the python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from backend.services.vector_store.faiss_store import FAISSStore

async def test_search():
    store = FAISSStore()
    query = "Screenshot"
    print(f"Searching for chunks from: {query}")
    results = await store.search(query, top_k=10)
    
    if not results:
        print("No results found.")
        return

    for i, res in enumerate(results):
        source = res['metadata'].get('source', 'unknown')
        if 'Screenshot' in source:
            print(f"\nResult {i+1} (Score: {res['score']}):")
            print(f"Content: {res['content'][:500]}...")
            print(f"Metadata: {res['metadata']}")

if __name__ == "__main__":
    asyncio.run(test_search())
