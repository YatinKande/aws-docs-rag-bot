import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

async def inspect_faiss():
    index_path = "data/indexes/faiss"
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if os.path.exists(index_path):
        vector_store = FAISS.load_local(
            index_path, 
            embeddings,
            allow_dangerous_deserialization=True
        )
        print(f"Total documents in FAISS: {len(vector_store.docstore._dict)}")
        
        # List unique sources
        sources_found = {}
        for doc in vector_store.docstore._dict.values():
            src = doc.metadata.get("source")
            if src not in sources_found:
                sources_found[src] = []
            sources_found[src].append(doc.page_content)
        
        print(f"Sources in FAISS: {list(sources_found.keys())}")
        
        for src in ['aws_s3.txt', 'aws_lambda.md', 'aws_services.csv', 'aws_config.json']:
            if src in sources_found:
                print(f"\n--- Chunks from {src} ---")
                for i, chunk in enumerate(sources_found[src]):
                    print(f"Chunk {i+1}: {chunk[:200]}...")
            else:
                print(f"\n--- {src} NOT FOUND in FAISS ---")
    else:
        print("FAISS index not found.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(inspect_faiss())
