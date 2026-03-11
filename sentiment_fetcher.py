import requests

def fetch_market_sentiment():
    """
    Fetches market sentiment from Crypto Fear & Greed Index as a proxy for retail risk sentiment.
    Returns (value, classification, recommendation)
    """
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            val = int(data['data'][0]['value'])
            classification = data['data'][0]['value_classification']
            
            # Risk recommendations based on sentiment
            recommendation = "Standard"
            if "Extreme Fear" in classification:
                recommendation = "Defensive (Tighten Stops)"
            elif "Extreme Greed" in classification:
                recommendation = "Caution (Reduce Sizes)"
                
            return val, classification, recommendation
    except Exception as e:
        print(f"Sentiment Fetch Error: {e}")
        
    return 50, "Neutral", "Standard"

if __name__ == "__main__":
    v, c, r = fetch_market_sentiment()
    print(f"Sentiment: {v} ({c}) -> {r}")
