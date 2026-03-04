import pickle
import os

faiss_pkl = "data/indexes/faiss/index.pkl"
if os.path.exists(faiss_pkl):
    try:
        with open(faiss_pkl, "rb") as f:
            data = pickle.load(f)
        
        sources = set()
        if isinstance(data, tuple) and len(data) >= 2:
            docstore = data[1]
            if isinstance(docstore, dict):
                # If it's a dict of objects with metadata
                for val in docstore.values():
                    if hasattr(val, 'metadata'):
                        src = val.metadata.get("source", "")
                        if src:
                            sources.add(src)
                    elif isinstance(val, dict):
                        # Some versions of FAISS use plain dicts
                        src = val.get("metadata", {}).get("source", "") or val.get("source", "")
                        if src:
                            sources.add(src)
        
        print("Final sources found in FAISS:", sources)
        
    except Exception as e:
        print(f"Error reading FAISS index: {e}")
else:
    print(f"FAISS index not found at {faiss_pkl}")
