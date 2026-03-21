import sys
from backtest import run_backtest_for_pair
from data_fetcher import fetch_data, get_macro_data

def main():
    pairs = ['EURNZD=X', 'GC=F']
    print("Fetching data...")
    market_data = fetch_data(pairs, period='6mo', interval='1h')
    macro = get_macro_data(period='6mo', interval='1h')
    
    for p in pairs:
        print(f"\n--- Backtesting {p} ---")
        if p in market_data:
            res = run_backtest_for_pair(p, market_data[p], macro_data=macro)
            if res:
                print(f"Trades: {res['trades']}")
                print(f"Win Rate: {res['win_rate']:.2%}")
                print(f"Sharpe: {res['sharpe']:.2f}")
                print(f"Return: {res['total_return']:.2%}")
                print(f"Max DD: {res['max_drawdown']:.2%}")
            else:
                print("No result.")

if __name__ == "__main__":
    main()
