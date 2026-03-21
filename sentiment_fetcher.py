import os
import requests
from dotenv import load_dotenv

# We will load transformer model on demand to save memory if not running sentiment
# from transformers import pipeline 

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def get_macro_headlines(query: str = "Federal Reserve OR ECB OR interest rates OR inflation") -> list:
    """
    Scrapes the top recent news headlines using SerpApi (Google News engine).
    Requires a valid SERPAPI_KEY in the environment.
    """
    if not SERPAPI_KEY:
        print(" [WARNING] SERPAPI_KEY not found. NLP Sentiment analysis will be disabled.")
        return []
        
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_news",
        "q": query,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "gl": "us",
        "tbs": "qdr:h6" # Only results from the last 6 hours
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        headlines = []
        for result in data.get("news_results", [])[:10]: # Top 10 headlines
            title = result.get("title")
            if title:
                headlines.append(title)
                
        return headlines
    except Exception as e:
        print(f" [SERPAPI ERROR] Failed to fetch headlines: {e}")
        return []

def calculate_nlp_sentiment_multiplier(headlines: list) -> float:
    """
    Passes headlines through the ProsusAI/finbert model.
    Returns a probability multiplier to be factored into the HMM Prediction.
    e.g. 1.0 (Neutral), 0.5 (Fear/Veto), 1.3 (Raging Bull)
    """
    if not headlines:
        return 1.0
        
    try:
        from transformers import pipeline
        # finbert categorizes as "positive", "negative", "neutral"
        nlp = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        
        results = nlp(headlines)
        
        score = 0
        for res in results:
            if res['label'] == 'positive':
                score += res['score']
            elif res['label'] == 'negative':
                score -= res['score']
                
        avg_score = score / len(headlines)
        
        # Map average score (-1.0 to 1.0) to a Multiplier (0.5x to 1.5x)
        # An intensely negative news flow (avg_score = -0.8) yields multiplier 0.6x (veto territory)
        multiplier = 1.0 + (avg_score * 0.5) 
        return max(0.5, min(1.5, multiplier))
        
    except Exception as e:
        print(f" [FINBERT ERROR] Failed to analyze sentiment: {e}")
        return 1.0

def get_realtime_sentiment_modifier(ticker: str) -> float:
    """
    Master function: specific to the ticker's base/quote or general macro.
    """
    query = "Federal Reserve interest rates"
    if 'EUR' in ticker:
        query = "ECB interest rates OR European economy"
    elif 'GBP' in ticker:
        query = "Bank of England interest rates OR UK economy"
    elif 'JPY' in ticker:
        query = "Bank of Japan interest rates OR JPY currency"
        
    headlines = get_macro_headlines(query)
    multiplier = calculate_nlp_sentiment_multiplier(headlines)
    return multiplier
