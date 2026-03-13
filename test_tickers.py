import yfinance as yf
import pandas as pd

tickers = {
    'US10Y': '^TNX',
    'UK10Y': 'GB10YT=RR',
    'GER10Y': 'DE10YT=RR',
    'DXY': 'DX-Y.NYB'
}

for name, symbol in tickers.items():
    print(f"Testing {name} ({symbol})...")
    try:
        df = yf.download(symbol, interval='1h', period='5d', progress=False)
        if not df.empty:
            print(f"  SUCCESS: Fetched {len(df)} rows.")
            print(df.tail(1))
        else:
            print(f"  FAILED: Empty DataFrame for {symbol}.")
    except Exception as e:
        print(f"  ERROR: {symbol} - {e}")
