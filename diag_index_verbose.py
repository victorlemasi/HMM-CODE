
import yfinance as yf
import pandas as pd
import numpy as np

def diag():
    print("DEBUG: Starting download...")
    # Fetch 1 day of hourly data
    fx = yf.download("EURUSD=X", interval="1h", period="2d", progress=False)
    yields = yf.download("^TNX", interval="1h", period="2d", progress=False)
    
    print(f"FX Index TZ: {fx.index.tz}, Shape: {fx.shape}")
    print(f"Yield Index TZ: {yields.index.tz}, Shape: {yields.shape}")
    
    # Check if indices match even remotely
    shared = fx.index.intersection(yields.index)
    print(f"Shared Indices: {len(shared)}")

    # Method 1: Reindex FX to Yield or vice versa
    fx_naive = fx.index.tz_localize(None)
    yield_naive = yields.index.tz_localize(None)
    
    fx_df = fx.copy()
    fx_df.index = fx_naive
    
    yield_df = yields.copy()
    yield_df.index = yield_naive
    
    reindexed = yield_df['Close'].reindex(fx_df.index)
    print(f"Reindexed NaNs: {reindexed.isna().sum()} / {len(reindexed)}")
    
    ffilled = reindexed.ffill().bfill()
    print(f"FFilled/Bfilled NaNs: {ffilled.isna().sum()} / {len(ffilled)}")
    
    if len(ffilled.dropna()) == len(fx_df):
        print("SUCCESS: Alignment with TZ-naive + ffill/bfill works.")
    else:
        print("FAILURE: Dropna still removes data.")

if __name__ == "__main__":
    diag()
