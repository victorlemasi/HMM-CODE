from backtest import run_backtest_for_pair
from data_fetcher import fetch_data, get_macro_data
from config import INTERVAL, PERIOD
import pandas as pd

tickers = ['EURUSD=X', 'GC=F']
print(f"Starting focused backtest for: {tickers}")

# Fetch data
data = fetch_data(tickers, interval='1h', period='6mo')
macro_data = get_macro_data(interval='1h', period='6mo')

results = []
for ticker in tickers:
    if ticker in data:
        metrics = run_backtest_for_pair(ticker, data[ticker], macro_data)
        if metrics:
            results.append(metrics)

if results:
    results_df = pd.DataFrame(results)
    print("\nFocused Backtest Results:")
    print(results_df)
else:
    print("No results generated.")
