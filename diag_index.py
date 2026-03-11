
import yfinance as yf
import pandas as pd
import numpy as np
from config import CURRENCY_PAIRS, COMMODITY_TICKERS, YIELD_TICKERS

def diag():
    print("Fetching EURUSD=X (FX)...")
    fx = yf.download("EURUSD=X", interval="1h", period="5d", progress=False)
    
    ticker_yield = YIELD_TICKERS['US10Y']
    print(f"Fetching {ticker_yield} (Yield)...")
    yields = yf.download(ticker_yield, interval="1h", period="5d", progress=False)
    
    print(f"\nFX Index Sample: {fx.index[:2]}")
    print(f"Yield Index Sample: {yields.index[:2]}")
    
    print(f"\nFX TZ: {fx.index.tz}")
    print(f"Yield TZ: {yields.index.tz}")
    
    # Try reindex
    try:
        reindexed = yields['Close'].reindex(fx.index)
        print(f"\nReindex Result NaNs: {reindexed.isna().sum()} / {len(reindexed)}")
    except Exception as e:
        print(f"\nReindex Failed: {e}")

    # Try alignment fix
    try:
        # 1. Force both to TZ-naive or same TZ
        fx_idx = fx.index.tz_localize(None) if fx.index.tz else fx.index
        yield_idx = yields.index.tz_localize(None) if yields.index.tz else yields.index
        
        yields_naive = yields.copy()
        yields_naive.index = yield_idx
        
        reindexed_fix = yields_naive['Close'].reindex(fx_idx).ffill()
        print(f"Fixed Reindex NaNs: {reindexed_fix.isna().sum()} / {len(reindexed_fix)}")
    except Exception as e:
        print(f"Alignment Fix Failed: {e}")

if __name__ == "__main__":
    diag()
