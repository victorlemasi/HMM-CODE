import os
import pandas as pd
from datetime import datetime
from data_fetcher import fetch_data, get_macro_data
from sentiment_fetcher import get_macro_headlines
from config import CURRENCY_PAIRS, INTERVAL, PERIOD

def check_data_integrity():
    print(f"Current System Time: {datetime.now()}")
    
    # 1. Check News Integrity
    print("\n--- NLP NEWS INTEGRITY CHECK ---")
    headlines = get_macro_headlines("Federal Reserve OR ECB OR interest rates")
    if headlines:
        print(f"Latest NLP Headlines (Top 3):")
        for h in headlines[:3]:
            print(f" - {h}")
    else:
        print(" [WARNING] No news headlines fetched. Check SerpApi key.")

    # 2. Check Yield Integrity (FRED)
    print("\n--- MACRO DATA INTEGRITY CHECK ---")
    macro_data = get_macro_data(INTERVAL, PERIOD)
    
    # Check US 10Y (DGS10)
    if 'DGS10' in macro_data:
        df_10y = macro_data['DGS10']
        print(f"US 10Y (FRED) Last Observation Date: {df_10y.index[-1]}")
        print(f"US 10Y (FRED) Current Value: {df_10y['Close'].iloc[-1]}%")
    else:
        print(" [WARNING] US 10Y data (DGS10) missing from macro fetch.")

    # Check DXY (Yahoo)
    if 'DX-Y.NYB' in macro_data:
        df_dxy = macro_data['DX-Y.NYB']
        print(f"DXY (Yahoo) Last Observation Date: {df_dxy.index[-1]}")
        print(f"DXY Current Value: {df_dxy['Close'].iloc[-1]}")
    else:
        print(" [WARNING] DXY data missing from macro fetch.")

    # Check Price Data
    print("\n--- PRICE DATA INTEGRITY CHECK ---")
    p_data = fetch_data(['EURUSD=X'], INTERVAL, PERIOD)
    if 'EURUSD=X' in p_data:
        df_price = p_data['EURUSD=X']
        print(f"EURUSD (Yahoo) Last Candle: {df_price.index[-1]}")
    else:
        print(" [WARNING] Price data fetch failed.")

if __name__ == "__main__":
    check_data_integrity()
