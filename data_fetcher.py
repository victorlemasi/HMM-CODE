import yfinance as yf
import pandas as pd
from typing import List, Dict
from config import CURRENCY_PAIRS, INTERVAL, PERIOD

def fetch_data() -> Dict[str, pd.DataFrame]:
    """
    Fetches historical data for the currency pairs defined in config.
    Returns a dictionary of DataFrames.
    """
    data = {}
    for pair in CURRENCY_PAIRS:
        print(f"Fetching data for {pair}...", end=" ")
        df = yf.download(pair, interval=INTERVAL, period=PERIOD, progress=False)
        if not df.empty:
            # Handle potential MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if 'Close' in df.columns:
                data[pair] = df
                print("Done.")
            else:
                print(f"Failed (Missing 'Close' column. Columns: {df.columns.tolist()})")
        else:
            print("Failed (Empty DataFrame)")
    return data

def get_returns_matrix(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Calculates percentage returns and joins them into a single matrix.
    """
    returns = {}
    for pair, df in data.items():
        # Ensure 'Close' is a Series
        close_prices = df['Close']
        if isinstance(close_prices, pd.DataFrame): # Should not happen with MultiIndex fix above
             close_prices = close_prices.iloc[:, 0]
        
        returns[pair] = close_prices.pct_change().dropna()
    
    # Align dates
    if not returns:
        return pd.DataFrame()
    
    returns_df = pd.DataFrame(returns).dropna()
    print(f"Returns Matrix built: {returns_df.shape}")
    return returns_df

if __name__ == "__main__":
    test_data = fetch_data()
    if test_data:
        returns = get_returns_matrix(test_data)
        print("Returns Matrix Preview:")
        print(returns.head())
        print(f"Matrix Shape: {returns.shape}")
