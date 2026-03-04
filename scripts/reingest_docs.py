import asyncio
from backend.services.retrieval.semantic_search import RetrievalService

async def reingest():
    service = RetrievalService()
    files = [
        ('aws_s3.txt', 'aws_s3.txt'),
        ('aws_lambda.md', 'aws_lambda.md'),
        ('aws_services.csv', 'aws_services.csv'),
        ('aws_config.json', 'aws_config.json')
    ]
    
    for filename, display_name in files:
        file_path = f"data/test_samples/{filename}"
        print(f"Re-ingesting {display_name} from {file_path}")
        await service.ingest_document(file_path, display_name)
    
    print("Re-ingestion complete.")

if __name__ == "__main__":
    asyncio.run(reingest())
