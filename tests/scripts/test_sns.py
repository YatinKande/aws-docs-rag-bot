import asyncio
import base64
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.llm_service import llm_service

async def test():
    img = '/Users/yatinkande/Documents/aws-rag-bot/data/uploads/temp/kelvin-ai-on-aws.png'
    with open(img, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    resp = await llm_service.analyze_image('What is the role of Amazon SNS?', data)
    print(resp)

if __name__ == "__main__":
    asyncio.run(test())
