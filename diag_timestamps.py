
import yfinance as yf
import pandas as pd
import numpy as np

def diag():
    print("Checking exact timestamps...")
    # Fetch 1 day of hourly data
    fx = yf.download("EURUSD=X", interval="1h", period="2d", progress=False)
    yields = yf.download("^TNX", interval="1h", period="2d", progress=False)
    
    fx_idx = fx.index.tz_localize(None) if fx.index.tz else fx.index
    yield_idx = yields.index.tz_localize(None) if yields.index.tz else yields.index
    
    print(f"FX Index sample: {fx_idx[:3].tolist()}")
    print(f"Yield Index sample: {yield_idx[:3].tolist()}")
    
    # Check for exact matches
    matches = fx_idx.isin(yield_idx)
    print(f"Exact Matches: {matches.sum()} / {len(fx_idx)}")
    
    # Check if rounding helps
    fx_rounded = fx_idx.round('H')
    yield_rounded = yield_idx.round('H')
    matches_rounded = fx_rounded.isin(yield_rounded)
    print(f"Rounded Matches: {matches_rounded.sum()} / {len(fx_idx)}")

if __name__ == "__main__":
    diag()
