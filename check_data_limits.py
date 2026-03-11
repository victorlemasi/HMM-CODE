
import yfinance as yf
import pandas as pd

def check_availability():
    tickers = ["^TNX", "CL=F", "HG=F", "GC=F"]
    for t in tickers:
        print(f"Checking {t} (1h, 60d)...")
        df = yf.download(t, interval="1h", period="60d", progress=False)
        print(f"  Bars: {len(df)}")
        
        print(f"Checking {t} (1h, 6mo)...")
        df_long = yf.download(t, interval="1h", period="6mo", progress=False)
        print(f"  Bars: {len(df_long)}")
        
        if len(df_long) == 0 and len(df) > 0:
            print(f"  [!] Yahoo Finance does NOT support 1h data for {t} at 6mo period.")
        elif len(df_long) < len(df):
            print(f"  [!] Data is truncated at 6mo.")
        print("-" * 30)

if __name__ == "__main__":
    check_availability()
