import yfinance as yf
import pandas as pd
import time
import requests
import io
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
    logger = logging.getLogger('yfinance')
    logger.disabled = True

    for pair in tickers:
        print(f"Fetching data for {pair}...", end=" ", flush=True)
        df = pd.DataFrame()
        
        # Retry mechanism (3 attempts)
        for attempt in range(3):
            try:
                import os, contextlib
                with open(os.devnull, 'w') as devnull:
                    with contextlib.redirect_stderr(devnull):
                        df = yf.download(pair, interval=interval, period=period, progress=False)
                
                if not df.empty:
                    break
            except Exception:
                pass
            
            if attempt < 2:
                time.sleep(1) # Wait before retry
        
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
            print("Failed (Empty DataFrame after 3 attempts)")
            
        time.sleep(0.5) # Anti-rate-limit delay between tickers
    return data

def fetch_fred_data(tickers: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Fetches economic data directly from FRED CSV exports.
    """
    data = {}
    for ticker in tickers:
        print(f"Fetching {ticker} from FRED...", end=" ", flush=True)
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ticker}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                df = pd.read_csv(io.BytesIO(response.content), index_col='observation_date', parse_dates=True)
                # Rename the value column to 'Close' and ensure numeric
                df.columns = ['Close']
                df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                df = df.dropna()
                data[ticker] = df
                print("Done.")
            else:
                print(f"Failed (HTTP {response.status_code})")
        except Exception:
            print("Failed (Connection Error)")
    return data

def get_macro_data(interval: str, period: str) -> Dict[str, pd.DataFrame]:
    """
    Fetches global macro tickers from Yahoo and FRED.
    """
    from config import COMMODITY_TICKERS, YIELD_TICKERS, FRED_TICKERS, POLICY_RATE_TICKERS
    
    # Yahoo Data
    macro_tickers = list(COMMODITY_TICKERS.values()) + list(YIELD_TICKERS.values())
    macro_tickers = list(set(macro_tickers))
    data = fetch_data(macro_tickers, interval=interval, period=period)
    
    # FRED Data
    from config import TIPS_TICKER, FRED_2Y_TICKERS
    fred_tickers = list(FRED_TICKERS.values()) + list(POLICY_RATE_TICKERS.values()) + [TIPS_TICKER] + list(FRED_2Y_TICKERS.values())
    fred_tickers = list(set(fred_tickers))
    if fred_tickers:
        fred_data = fetch_fred_data(fred_tickers)
        data.update(fred_data)
        
    return data

def get_returns_matrix(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Calculates percentage returns and joins them into a single matrix.
    Safe-guarded against empty DataFrames and alignment issues.
    """
    returns = {}
    for pair, df in data.items():
        if df is None or df.empty:
            continue
            
        # Ensure 'Close' exists and is handled as a Series
        if 'Close' not in df.columns:
            continue
            
        close_prices = df['Close']
        if isinstance(close_prices, pd.DataFrame):
             close_prices = close_prices.iloc[:, 0]
        
        # Calculate log returns for better statistical properties in clustering/HMM
        s = np.log(close_prices / close_prices.shift(1)).dropna()
        if not s.empty:
            returns[pair] = s
    
    # Align dates
    if not returns:
        return pd.DataFrame()
    
    returns_df = pd.DataFrame(returns).dropna()
    if not returns_df.empty:
        print(f"Returns Matrix built: {returns_df.shape}")
    return returns_df

def fetch_watchdog_data(tickers: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Fetches latest 1-minute data for jump detection.
    """
    return fetch_data(tickers, interval='1m', period='1d')

if __name__ == "__main__":
    test_data = fetch_data()
    if test_data:
        returns = get_returns_matrix(test_data)
        print("Returns Matrix Preview:")
        print(returns.head())
        print(f"Matrix Shape: {returns.shape}")
