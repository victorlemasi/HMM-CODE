
import yfinance as yf
import pandas as pd
import numpy as np
from hmm_analysis import detect_breakout

def debug_detect():
    print("Fetching data...")
    pair = "EURUSD=X"
    df = yf.download(pair, interval="1h", period="10d", progress=False)
    macro_data = {
        "^TNX": yf.download("^TNX", interval="1h", period="10d", progress=False),
        "CL=F": yf.download("CL=F", interval="1h", period="10d", progress=False)
    }
    
    print(f"Main DF Shape: {df.shape}")
    print(f"Yield DF Shape: {macro_data['^TNX'].shape}")
    
    try:
        # Pass a small slice to simulate backtest window
        is_breakout, direction, regime, _ = detect_breakout(df.iloc[-400:], ticker=pair, macro_data=macro_data)
        print(f"SUCCESS: Regime={regime}, Direction={direction}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    debug_detect()
