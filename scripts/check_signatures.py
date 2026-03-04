from langchain_community.vectorstores import LanceDB
from langchain_milvus import Milvus
from langchain_huggingface import HuggingFaceEmbeddings
import lancedb
import os

print("Testing LanceDB and Milvus constructor signatures...")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

try:
    # Test LanceDB
    db = lancedb.connect("lancedb_test")
    # Check if we can instantiate it
    try:
        store = LanceDB(connection=db, embedding=embeddings, table_name="test")
        print("LanceDB constructor with 'embedding' worked")
    except TypeError as e:
        print(f"LanceDB constructor with 'embedding' failed: {e}")
        try:
                store = LanceDB(connection=db, embedding_function=embeddings, table_name="test")
                print("LanceDB constructor with 'embedding_function' worked")
        except TypeError as e2:
                print(f"LanceDB constructor with 'embedding_function' failed: {e2}")

    # Test Milvus
    try:
        # Note: Milvus Lite might need aURI
        store = Milvus(embedding_function=embeddings, connection_args={"uri": "./milvus_test.db"}, collection_name="test")
        print("Milvus constructor with 'embedding_function' worked")
    except TypeError as e:
        print(f"Milvus constructor with 'embedding_function' failed: {e}")
        try:
             store = Milvus(embeddings=embeddings, connection_args={"uri": "./milvus_test.db"}, collection_name="test")
             print("Milvus constructor with 'embeddings' worked")
        except TypeError as e2:
             print(f"Milvus constructor with 'embeddings' failed: {e2}")

except Exception as e:
    print(f"General error: {e}")
