
import yfinance as yf
import pandas as pd
import numpy as np
from config import YIELD_TICKERS

def diag():
    period = "6mo"
    interval = "1h"
    print(f"Fetching EURUSD=X (FX) for {period}...")
    fx = yf.download("EURUSD=X", interval=interval, period=period, progress=False)
    
    ticker_yield = YIELD_TICKERS['US10Y']
    print(f"Fetching {ticker_yield} (Yield) for {period}...")
    yields = yf.download(ticker_yield, interval=interval, period=period, progress=False)
    
    print(f"\nFX: Start={fx.index.min()}, End={fx.index.max()}, Length={len(fx)}")
    print(f"Yield: Start={yields.index.min()}, End={yields.index.max()}, Length={len(yields)}")
    
    # Check intersection after TZ cleaning
    fx.index = fx.index.tz_localize(None) if fx.index.tz else fx.index
    yields.index = yields.index.tz_localize(None) if yields.index.tz else yields.index
    
    shared = fx.index.intersection(yields.index)
    print(f"Shared Indices Count: {len(shared)}")
    
    # If 0, check if yields has any data at all
    if len(yields) > 0:
         print(f"Yield Index Sample: {yields.index[:5]}")
         print(f"FX Index Sample: {fx.index[:5]}")

if __name__ == "__main__":
    diag()
