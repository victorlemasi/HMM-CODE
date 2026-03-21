import pandas as pd
from data_fetcher import fetch_data, get_macro_data
from backtest import run_backtest_for_pair

TICKS = ['EURUSD=X', 'USDJPY=X']
INTERVAL = '1h'
PERIOD = '6mo'

def main():
    print(f"Testing recovery for {TICKS}...")
    all_data = fetch_data(TICKS, period=PERIOD, interval=INTERVAL)
    macro = get_macro_data(interval=INTERVAL, period=PERIOD)
    
    for symbol in TICKS:
        if symbol not in all_data or all_data[symbol] is None or all_data[symbol].empty:
            print(f"  {symbol}: SKIPPED (no data)")
            continue
            
        print(f"Backtesting {symbol}...")
        res = run_backtest_for_pair(symbol, all_data[symbol], macro_data=macro)
        if res:
            print(f"  Trades: {res['trades']} | Return: {res['total_return']:.2%}")
        else:
            print(f"  {symbol} run failed.")

if __name__ == "__main__":
    main()
