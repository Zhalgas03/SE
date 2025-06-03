import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PERPLEXITY_API_KEY")

if not API_KEY:
    print("❌ PERPLEXITY_API_KEY not found")
    exit()

response = requests.get(
    "https://api.perplexity.ai/models",
    headers={"Authorization": f"Bearer {API_KEY}"}
)

print("📡 Status:", response.status_code)
print("📦 Response:\n", response.text)
