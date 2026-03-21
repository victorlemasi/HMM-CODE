import pandas as pd
import numpy as np
from data_fetcher import fetch_micro_cvd_data

def get_micro_cvd_slope(ticker: str) -> float:
    """
    Phase 4: High-Frequency Micro-CVD Engine.
    Downloads the last 7 days of 1-minute OHLCV data to build a highly granular
    Limit-Order Order Flow proxy, entirely bypassing the 1-hour smoothing.
    
    Returns the slope (momentum) of the CVD over the most recent 60-minute window
    to detect real-time heavy volume trapping.
    """
    df = fetch_micro_cvd_data(ticker)
    
    if df is None or df.empty or 'Volume' not in df.columns or 'Close' not in df.columns:
        return 0.0
        
    # Some FX pairs on Yahoo have 0 volume. If max volume is 0, we can't calculate CVD
    if df['Volume'].max() == 0:
        return 0.0
        
    # Calculate 1-Minute Intraday Intensity (Aggressor proxy)
    # Delta = Volume * ((Close - Low) - (High - Close)) / (High - Low)
    # Simplified: Volume * ((2 * Close - High - Low) / (High - Low + 1e-9))
    
    high = df['High']
    low = df['Low']
    close = df['Close']
    volume = df['Volume']
    
    multiplier = (2 * close - high - low) / (high - low + 1e-9)
    micro_delta = volume * multiplier
    
    # Cumulative Sum to build the CVD line
    cvd = micro_delta.cumsum()
    
    # We want the slope of the CVD over the last 60 minutes (1 hour) to see
    # if institutional limit orders are currently stepping in heavily.
    if len(cvd) >= 60:
        recent_slope = cvd.iloc[-1] - cvd.iloc[-60]
    elif len(cvd) > 2:
        recent_slope = cvd.iloc[-1] - cvd.iloc[0]
    else:
        recent_slope = 0.0
        
    return recent_slope
