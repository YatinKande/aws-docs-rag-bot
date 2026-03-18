import asyncio
import base64
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.llm_service import llm_service

async def test_analyze_image(image_path, question):
    print(f"\n--- Testing Image: {os.path.basename(image_path)} ---")
    print(f"Question: {question}")
    
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} not found.")
        return

    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    try:
        response = await llm_service.analyze_image(question, image_base64)
        print(f"Response:\n{response}")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    # Test 1: Architecture diagram
    await test_analyze_image(
        "/Users/yatinkande/Documents/aws-rag-bot/data/uploads/temp/kelvin-ai-on-aws.png",
        "What is the role of Kinesis Data Streams?"
    )

if __name__ == "__main__":
    asyncio.run(main())
