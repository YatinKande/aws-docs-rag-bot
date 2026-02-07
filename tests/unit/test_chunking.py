import pytest
from backend.utils.chunking import Chunker

def test_chunking():
    chunker = Chunker(chunk_size=50, chunk_overlap=10)
    text = "This is a long sentence that should be split into multiple chunks for better retrieval performance."
    
    chunks = chunker.split_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 60 for c in chunks) # Allow some overhead

def test_code_chunking():
    chunker = Chunker(chunk_size=50, chunk_overlap=10)
    code = """def hello_world():
    print("Hello, world!")
    return True"""
    
    chunks = chunker.split_code(code, "py")
    assert len(chunks) >= 1
