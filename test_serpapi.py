import requests
import os
from dotenv import load_dotenv

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def test_serpapi():
    if not SERPAPI_KEY:
        print(" [CRITICAL] No SERPAPI_KEY found in your .env file!")
        return
        
    print(f"Testing SerpApi with Key: {SERPAPI_KEY[:5]}...{SERPAPI_KEY[-5:]}")
    params = {
        "engine": "google_news",
        "q": "Federal Reserve",
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": "us",
        "tbs": "qdr:h"
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        headlines = [r.get("title") for r in data.get("news_results", [])[:3]]
        
        if headlines:
            print(f" [SUCCESS] SerpApi is REACHABLE. Top Headlines: {headlines}")
        else:
            print(" [WARNING] Connection OK, but no news headlines found for 'Federal Reserve'.")
    except Exception as e:
        print(f" [CRITICAL ERROR] SerpApi connection FAILED: {e}")

if __name__ == "__main__":
    test_serpapi()
