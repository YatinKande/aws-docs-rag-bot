import os
import sys
from langchain_milvus import Milvus
from langchain_community.embeddings import HuggingFaceEmbeddings

print("Step 1: Loading embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("Step 2: Connecting to Milvus Lite (uri='./milvus_test.db')...")
try:
    vector_store = Milvus(
        embedding_function=embeddings,
        connection_args={"uri": "./milvus_test.db"},
        collection_name="test_collection",
        auto_id=True,
        drop_old=True
    )
    print("Step 3: Success! Connection established.")
    
    print("Step 4: Testing add_texts...")
    vector_store.add_texts(["Hello world"], [{"source": "test"}])
    print("Step 5: Success! Data added.")
    
    if os.path.exists("./milvus_test.db"):
        print("Step 6: Verified! milvus_test.db exists.")
    else:
        print("Step 6: ERROR! milvus_test.db NOT found.")

except Exception as e:
    print(f"FAILED: {e}")
