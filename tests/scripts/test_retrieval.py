import asyncio
from backend.services.retrieval.semantic_search import RetrievalService

async def test_retrieval():
    service = RetrievalService()
    queries = [
        "SageMaker",
        "What are the storage classes available in Amazon S3?",
        "What are the benefits of AWS Lambda?",
        "Which AWS service is NOT free tier eligible?",
        "instance_type and image_id in the JSON configuration"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = await service.semantic_search(query)
        print(f"Results found: {len(results)}")
        for i, res in enumerate(results):
            print(f"  {i+1}. Source: {res['metadata'].get('source')} - Score: {res.get('hybrid_score', 'N/A')}")
            print(f"     Content: {res['content'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
