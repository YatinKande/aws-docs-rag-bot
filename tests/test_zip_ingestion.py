import os
import asyncio
import zipfile
import tempfile
import json
from unittest.mock import MagicMock, patch
from backend.services.document_processor import DocumentProcessor

async def test_zip_ingestion():
    processor = DocumentProcessor()
    
    # Mock LLM and Vision calls to avoid real API dependencies
    processor._llm_service = MagicMock()
    processor._llm_service.describe_image = asyncio.CoroutineMock(return_value="Mocked visual description")
    
    # Create a dummy zip file
    with tempfile.TemporaryDirectory() as tmp_data_dir:
        zip_path = os.path.join(tmp_data_dir, "test_ingestion.zip")
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # 1. Plain text file
            zf.writestr("folder1/test.txt", "Hello world from txt")
            
            # 2. JSON file
            zf.writestr("folder1/test.json", json.dumps({"key": "value"}))
            
            # 3. MD file in subfolder
            zf.writestr("folder1/subfolder/readme.md", "# Readme\nThis is a markdown file")
            
            # 4. Dummy PDF (just enough to not crash pypdf/unstructured if they are called)
            # Actually, we can mock process_pdf_smart if we want to be safe
            zf.writestr("dummy.pdf", "Dummy PDF content")
            
        print(f"Created test zip at {zip_path}")
        
        # Patch methods that depend on external libraries or complex logic if necessary
        # We want to verify _process_zip_file calls process_file for each entry.
        
        with patch.object(DocumentProcessor, 'process_file', wraps=processor.process_file) as mock_process:
            # We also need to avoid real OCR/etc if they trigger
            with patch.object(DocumentProcessor, '_process_universal', return_value="Universal content"):
                with patch.object(DocumentProcessor, '_process_pdf_smart', return_value="PDF content"):
                    
                    text = await processor._process_zip_file(zip_path)
                    
                    print(f"\nExtracted Text Length: {len(text)}")
                    print(f"Extracted Text Snippet: {text[:200]}...")
                    
                    # Verify calls
                    print(f"Total files processed: {mock_process.call_count}")
                    
                    # Check if all expected files were processed
                    processed_filenames = [call.args[1] for call in mock_process.call_args_list]
                    print(f"Processed filenames: {processed_filenames}")
                    
                    assert "test.txt" in processed_filenames
                    assert "test.json" in processed_filenames
                    assert "readme.md" in processed_filenames
                    assert "dummy.pdf" in processed_filenames
                    
                    assert "Hello world from txt" in text
                    assert '"key": "value"' in text
                    # readme.md content should be there
                    assert "This is a markdown file" in text
                    
                    print("\n✅ Zip Ingestion Test Passed!")

if __name__ == "__main__":
    # Mock asyncio.CoroutineMock if using older python, but here we can just use MagicMock with async
    if not hasattr(asyncio, "CoroutineMock"):
        # Simple manual coroutine mock for older systems if needed
        class AsyncMock(MagicMock):
            async def __call__(self, *args, **kwargs):
                return super(AsyncMock, self).__call__(*args, **kwargs)
        asyncio.CoroutineMock = AsyncMock

    asyncio.run(test_zip_ingestion())
