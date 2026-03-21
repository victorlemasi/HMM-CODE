import warnings
import numpy as np
import pandas as pd
from datetime import datetime
import os

warnings.filterwarnings("ignore")

from data_fetcher import fetch_data
from hmm_analysis import detect_breakout

def check_mtf_alignment():
    print("--- MTF ALIGNMENT AUDIT: EURUSD=X ---")
    
    # 1. Fetch Daily Data
    daily_data = fetch_data(["EURUSD=X"], period="1y", interval="1d")
    df_d = daily_data["EURUSD=X"]
    
    # 2. Fetch Hourly Data (aligned with the backtest period)
    hourly_data = fetch_data(["EURUSD=X"], period="6mo", interval="1h")
    df_h = hourly_data["EURUSD=X"]
    
    print(f"Daily Bars: {len(df_d)} | Hourly Bars: {len(df_h)}")
    
    # Analyze Daily Trend via HMM
    # We'll just run a quick sweep of the daily trend
    regime_d, prob_d, direction_d, _, _, _, _ = detect_breakout(df_d, ticker="EURUSD=X")
    print(f"Current Daily Regime: {regime_d} | Direction: {direction_d} | Conf: {prob_d:.2f}")

if __name__ == "__main__":
    check_mtf_alignment()
