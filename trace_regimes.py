"""
Comprehensive regime tracer: runs detect_breakout for every bar in the backtest
and reports the distribution of regimes.
"""
import sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import os, pickle

sys.path.insert(0, r"c:\Users\lenovo\Downloads\scanner\Currency-Pair-Scanner-Analysis")

from data_fetcher import fetch_data, get_macro_data
from hmm_analysis import detect_breakout, calculate_atr
from config import HMM_MODELS_PATH

TRAIN_WINDOW = 1200
STEP_SIZE = 24

symbol = 'AUDJPY=X'
df_all = fetch_data([symbol], period='6mo', interval='1h').get(symbol)
macro  = get_macro_data(interval='1h', period='6mo')

df_all['Returns'] = np.log(df_all['Close'] / df_all['Close'].shift(1))
df_all['ATR']     = calculate_atr(df_all)
df_all = df_all.dropna()

model_file = os.path.join(HMM_MODELS_PATH, f"EURUSD_hmm.pkl")
with open(model_file, 'rb') as f:
    pretrained_model = pickle.load(f)

regime_counts = {}
total_steps = 0

print(f"Tracing {symbol}...")

for t in range(TRAIN_WINDOW, len(df_all), STEP_SIZE):
    train_slice = df_all.iloc[t - TRAIN_WINDOW:t].copy()
    try:
        is_bo, direction, regime, _, _, prob = detect_breakout(
            train_slice, ticker=symbol, macro_data=macro, model=pretrained_model
        )
        regime_counts[regime] = regime_counts.get(regime, 0) + 1
        total_steps += 1
    except Exception as e:
        print(f"Error at t={t}: {e}")

print(f"\nResults for {symbol} ({total_steps} steps):")
for r, c in regime_counts.items():
    print(f"  {r}: {c} ({c/total_steps*100:.1f}%)")
