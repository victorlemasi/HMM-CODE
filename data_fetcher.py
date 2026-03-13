import yfinance as yf
import pandas as pd
from typing import List, Dict
from config import CURRENCY_PAIRS, INTERVAL, PERIOD

def fetch_data(tickers: List[str], interval: str, period: str) -> Dict[str, pd.DataFrame]:
    """
    Fetches historical data for the given tickers.
    Returns a dictionary of DataFrames.
    """
    data = {}
    if not tickers:
        return data
        
    # Ensure tickers is a list (handle single ticker case)
    if isinstance(tickers, str):
        tickers = [tickers]

    import logging
    yf.set_tz_cache_location('yfinance_cache') # Keep this just in case
    logger = logging.getLogger('yfinance')
    logger.disabled = True

    for pair in tickers:
        print(f"Fetching data for {pair}...", end=" ")
        
        # Suppress yfinance error printing
        try:
            df = yf.download(pair, interval=interval, period=period, progress=False, show_errors=False)
        except Exception:
            df = pd.DataFrame()
        if hasattr(df, 'empty') and not df.empty:
            # Handle potential MultiIndex columns or multi-level downloads
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if 'Close' in df.columns:
                df['Returns'] = df['Close'].pct_change()
                data[pair] = df
                print("Done.")
            else:
                print(f"Failed (Missing 'Close' column. Columns: {df.columns.tolist()})")
        else:
            print("Failed (Empty DataFrame)")
    return data

def get_macro_data(interval: str, period: str) -> Dict[str, pd.DataFrame]:
    """
    Fetches global macro tickers (Yields, Commodities) defined in config.
    """
    from config import COMMODITY_TICKERS, YIELD_TICKERS
    macro_tickers = list(COMMODITY_TICKERS.values()) + list(YIELD_TICKERS.values())
    # Remove duplicates
    macro_tickers = list(set(macro_tickers))
    return fetch_data(macro_tickers, interval=interval, period=period)

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
