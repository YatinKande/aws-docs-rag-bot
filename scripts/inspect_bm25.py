import pickle
import os

def inspect_bm25():
    index_path = "data/indexes/bm25/bm25_index.pkl"
    if os.path.exists(index_path):
        with open(index_path, "rb") as f:
            data = pickle.load(f)
            metadatas = data["metadatas"]
            print(f"Total chunks in BM25: {len(metadatas)}")
            sources = set(m.get("source") for m in metadatas)
            print(f"Sources in BM25: {sources}")
            
            for m in metadatas:
                if m.get("source") == "aws_services.csv":
                    print(f"Found chunk for aws_services.csv: {m}")
    else:
        print("BM25 index not found.")

if __name__ == "__main__":
    inspect_bm25()
