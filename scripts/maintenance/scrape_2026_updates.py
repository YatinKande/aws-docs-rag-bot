import requests
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime

os.makedirs("data/scraped/2026_updates", exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RAGBot/1.0)"
}

def scrape_page(url: str, label: str) -> str:
    try:
        r = requests.get(
            url, headers=HEADERS, timeout=15
        )
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style",
                          "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if l.strip()]
        clean = "\n".join(lines)
        print(f"✅ Scraped: {label} ({len(clean)} chars)")
        return clean
    except Exception as e:
        print(f"❌ Failed: {label} — {e}")
        return ""

def save_doc(content, filepath, url, category):
    if not content:
        return
    header = f"""SOURCE: {url}
CATEGORY: {category}
SCRAPED: {datetime.now().isoformat()}
YEAR: 2026
{'='*60}

"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + content)
    print(f"💾 Saved: {filepath}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2026 AWS NEWS & ANNOUNCEMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
sources_2026 = {

    # What's New feed
    "whats_new_2026": "https://aws.amazon.com/new/",

    # Weekly roundups 2026
    "weekly_roundup_mar2026": "https://aws.amazon.com/blogs/aws/aws-weekly-roundup-openai-partnership-aws-elemental-inference-strands-labs-and-more-march-2-2026/",
    "weekly_roundup_jan2026": "https://aws.amazon.com/blogs/aws/aws-weekly-roundup-kiro-cli-latest-features-aws-european-sovereign-cloud-ec2-x8i-instances-and-more-january-19-2026/",

    # Major 2026 launches
    "european_sovereign_cloud": "https://aws.amazon.com/blogs/aws/aws-european-sovereign-cloud-is-now-generally-available/",
    "bedrock_openai_partnership": "https://aws.amazon.com/blogs/aws/openai-and-amazon-announce-strategic-partnership/",
    "bedrock_reinforcement_finetuning": "https://aws.amazon.com/blogs/aws/amazon-bedrock-reinforcement-fine-tuning/",
    "strands_labs": "https://aws.amazon.com/blogs/aws/introducing-strands-labs/",

    # re:Invent 2025 announcements (affect 2026)
    "reinvent_2025_announcements": "https://aws.amazon.com/blogs/aws/top-announcements-of-aws-reinvent-2025/",
    "reinvent_2025_keynote_summary": "https://aws.amazon.com/blogs/aws/aws-reinvent-2025-andy-jassy-keynote/",

    # New services in 2026
    "s3_vectors": "https://aws.amazon.com/blogs/aws/introducing-amazon-s3-vectors/",
    "graviton5": "https://aws.amazon.com/blogs/aws/new-amazon-ec2-m9g-instances-powered-by-aws-graviton5/",
    "bedrock_agentcore": "https://aws.amazon.com/blogs/aws/amazon-bedrock-agentcore/",
    "amazon_quick_suite": "https://aws.amazon.com/blogs/aws/introducing-amazon-quick-suite/",

    # AWS CLI v2 updates
    "aws_cli_v2_2026": "https://aws.amazon.com/blogs/developer/aws-cli-v2-new-output-formats/",

    # Bedrock updates 2026
    "bedrock_projects_api": "https://aws.amazon.com/blogs/aws/openai-compatible-projects-api-amazon-bedrock/",
    "bedrock_latest_features": "https://aws.amazon.com/bedrock/whats-new/",

    # Service limit updates 2026
    "aws_service_limits_2026": "https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html",

    # re:Post community goldmine
    "repost_lambda": "https://repost.aws/tags/TAe-JEiwohTpGRJOWTKJ7kOQ/aws-lambda",
    "repost_s3": "https://repost.aws/tags/TAdlH2_-yuTJGLbHf2GEEJfw/amazon-s3",
    "repost_bedrock": "https://repost.aws/tags/TANgMUdRouSoaUNSGEbj5Gvg/amazon-bedrock",
    "repost_ec2": "https://repost.aws/tags/TAe2apSjxyRzGaKJHjr1XREA/amazon-ec2",
}

# Scrape all sources
results = {"success": [], "failed": []}

for name, url in sources_2026.items():
    content = scrape_page(url, name)
    if content:
        filepath = f"data/scraped/2026_updates/{name}.txt"
        save_doc(content, filepath, url, "AWS 2026 Updates")
        results["success"].append(name)
    else:
        results["failed"].append(name)
    time.sleep(2)

# Save index
index = {
    "created": datetime.now().isoformat(),
    "total_scraped": len(results["success"]),
    "failed": results["failed"],
    "files": results["success"]
}
with open(
    "data/scraped/2026_updates/index_2026.json", "w"
) as f:
    json.dump(index, f, indent=2)

print(f"\n✅ Done! {len(results['success'])} scraped")
print(f"❌ Failed: {len(results['failed'])}")
print(f"Failed list: {results['failed']}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UPLOAD ALL TO S3
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import boto3

s3 = boto3.client("s3", region_name="us-east-1")
BUCKET = "cloud-intelligence-rag-store"

uploaded = 0
for fname in os.listdir("data/scraped/2026_updates"):
    if not fname.endswith(".txt"):
        continue
    local = f"data/scraped/2026_updates/{fname}"
    key = f"documents/scraped/2026_updates/{fname}"
    try:
        s3.upload_file(local, BUCKET, key)
        print(f"☁️  S3: {key}")
        uploaded += 1
    except Exception as e:
        print(f"❌ S3 failed {fname}: {e}")

print(f"\n☁️  Uploaded {uploaded} files to S3")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INGEST INTO RAG BOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import requests as req

ingested = 0
for fname in os.listdir("data/scraped/2026_updates"):
    if not fname.endswith(".txt"):
        continue
    local = f"data/scraped/2026_updates/{fname}"
    try:
        with open(local, "rb") as f:
            r = req.post(
                "http://localhost:8000/api/v1/documents/upload",
                files={"file": (fname, f, "text/plain")},
                timeout=120
            )
        if r.status_code == 200:
            print(f"🤖 BOT: {fname}")
            ingested += 1
        else:
            print(f"❌ BOT failed {fname}: {r.status_code}")
    except Exception as e:
        print(f"❌ BOT error {fname}: {e}")
    time.sleep(2)

print(f"\n🤖 Ingested {ingested} files into RAG bot")
print("\n✅ ALL DONE!")
print(f"Scraped: {len(results['success'])}")
print(f"S3: {uploaded}")
print(f"Bot: {ingested}")
