
import yfinance as yf
import pandas as pd

def check_dates():
    tickers = ["EURUSD=X", "^TNX", "CL=F"]
    for t in tickers:
        print(f"Checking {t} (1h, 6mo)...")
        df = yf.download(t, interval="1h", period="6mo", progress=False)
        if not df.empty:
            print(f"  Range: {df.index.min()} to {df.index.max()}")
            print(f"  Count: {len(df)}")
        else:
            print("  NO DATA")
        print("-" * 30)

if __name__ == "__main__":
    check_dates()
