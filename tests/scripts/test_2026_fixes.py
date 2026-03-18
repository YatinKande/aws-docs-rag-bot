import requests as req
import json

questions = [
    ("Q1", "What is AWS European Sovereign Cloud and when did it launch?"),
    ("Q2", "What is the OpenAI and AWS partnership announced in 2026?")
]

for id, q in questions:
    print(f"\n--- {id}: {q} ---")
    payload = {"query": q, "selected_source": "docs", "selected_db": "faiss"}
    try:
        r = req.post("http://localhost:8000/api/v1/chat/", json=payload, timeout=120)
        if r.status_code == 200:
            data = r.json()
            print(f"ANSWER: {data['answer']}")
        else:
            print(f"❌ Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Failed to reach backend: {e}")
