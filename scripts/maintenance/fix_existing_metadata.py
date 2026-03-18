import os
import sqlite3
import requests as req
import time

DB_PATH = "data/database/sql_app.db"
BASE_URL = "http://localhost:8000/api/v1"

# Directories where original scraped files might be
SCRAPE_DIRS = [
    "data/scraped/2026_updates",
    "data/scraped/blogs",
    "data/scraped/faqs",
    "data/scraped/labs"
]

def find_file_locally(filename):
    for d in SCRAPE_DIRS:
        full_path = os.path.join(d, filename)
        if os.path.exists(full_path):
            return full_path
    return None

def repair_and_retry():
    if not os.path.exists(DB_PATH):
        print(f"❌ DB not found at {DB_PATH}")
        return

    print("🔌 Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Update source_path for files that are missing but exist in scrape dirs
    cursor.execute("SELECT id, filename, source_path FROM documents WHERE status = 'completed' OR status = 'failed'")
    rows = cursor.fetchall()
    
    updated_count = 0
    to_retry = []

    for doc_id, filename, source_path in rows:
        # Check if the current source_path exists
        if not source_path or not os.path.exists(source_path):
            local_path = find_file_locally(filename)
            if local_path:
                print(f"🛠  Fixing path for {filename}: {local_path}")
                cursor.execute("UPDATE documents SET source_path = ? WHERE id = ?", (local_path, doc_id))
                updated_count += 1
                to_retry.append((doc_id, filename))
            else:
                print(f"⚠️  Could not find local file for {filename}")
        else:
            # If path is okay, still check if it's a 2026 doc that needs metadata refresh
            is_2026 = any(x in filename for x in ["2025", "2026", "sovereign", "openai"])
            if is_2026:
                to_retry.append((doc_id, filename))

    conn.commit()
    print(f"✅ Updated {updated_count} source paths in DB.")

    # 2. Trigger retries via API
    print(f"⚙️  Triggering {len(to_retry)} retries...")
    for i, (doc_id, filename) in enumerate(to_retry):
        print(f"[{i+1}/{len(to_retry)}] Retrying {filename}...")
        try:
            r = req.post(f"{BASE_URL}/documents/{doc_id}/retry", timeout=10)
            if r.status_code == 200:
                print(f"  ✅ Success")
            else:
                print(f"  ❌ Failed: {r.text}")
        except Exception as e:
            print(f"  ❌ API Error: {e}")
        time.sleep(1)

    conn.close()
    print("\n🏁 Repair process complete.")

if __name__ == "__main__":
    repair_and_retry()
