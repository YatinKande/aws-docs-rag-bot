import requests
from bs4 import BeautifulSoup

urls_to_fix = {
    "european_sovereign_cloud.txt": "https://aws.amazon.com/blogs/aws/the-aws-european-sovereign-cloud-is-now-generally-available/",
    "bedrock_openai_partnership.txt": "https://aws.amazon.com/blogs/aws/aws-weekly-roundup-openai-partnership-aws-elemental-inference-strands-labs-and-more-march-2-2026/"
}

HEADERS = {"User-Agent": "Mozilla/5.0"}

for filename, url in urls_to_fix.items():
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script","style","nav",
                      "footer","header"]):
        tag.decompose()
    text = "\n".join(
        l for l in 
        soup.get_text(separator="\n").splitlines() 
        if l.strip()
    )
    
    header = f"SOURCE: {url}\nYEAR: 2026\n{'='*60}\n\n"
    
    with open(
        f"data/scraped/2026_updates/{filename}", "w"
    ) as f:
        f.write(header + text)
    print(f"✅ Re-scraped: {filename} ({len(text)} chars)")
