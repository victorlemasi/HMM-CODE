"""
Quick diagnostic: runs detect_breakout on EURUSD's most recent 1200 bars
and prints every intermediate result so we can pinpoint the failure.
"""
import sys, traceback
import pandas as pd
import numpy as np

sys.path.insert(0, r"c:\Users\lenovo\Downloads\scanner\Currency-Pair-Scanner-Analysis")

from data_fetcher import fetch_data, get_macro_data
from hmm_analysis import detect_breakout, calculate_atr

# ── 1. Fetch data ────────────────────────────────────────────────────────────
df = fetch_data(['EURUSD=X'], period='6mo', interval='1h').get('EURUSD=X')
if df is None or df.empty:
    print("ERROR: no price data"); sys.exit(1)

macro = get_macro_data(interval='1h', period='6mo')

# ── 2. Build a 1200-bar slice (same as backtest does) ───────────────────────
df['Returns'] = np.log(df['Close'] / df['Close'].shift(1))
df['ATR']     = calculate_atr(df)
df = df.dropna()
slice_df = df.iloc[-1200:].copy()

print(f"Slice shape: {slice_df.shape}")

# ── 3. Call detect_breakout and capture every exception ─────────────────────
try:
    result = detect_breakout(slice_df, ticker='EURUSD=X', macro_data=macro, model=None)
    is_bo, direction, regime, _, atr, prob = result
    print(f"\n✓ Result: regime={regime}, direction={direction}, prob={prob:.4f}, is_breakout={is_bo}")
except Exception as e:
    print(f"\n✗ detect_breakout RAISED: {type(e).__name__}: {e}")
    traceback.print_exc()
