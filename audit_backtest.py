import warnings
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import os

# Suppress hmmlearn noise
warnings.filterwarnings("ignore")

from data_fetcher import fetch_data, get_macro_data
from hmm_analysis import detect_breakout, get_dynamic_exit_levels, calculate_atr, get_trigger_price, calculate_z_score, calculate_mahalanobis_distance
from macro_bouncer import (
    check_fundamental_gatekeeper, get_macro_weight,
    get_yield_spread_momentum, check_macro_alignment
)
from config import CURRENCY_PAIRS, MAJORS_FIX_LIST, WATCHDOG_TICKERS, WATCHDOG_JUMP_THRESHOLDS, LUNCH_ZONE, MAJORS_MIN_CONFIDENCE, MINORS_MIN_CONFIDENCE

# CONFIG FOR AUDIT
AUDIT_TICKER = "EURUSD=X"
BACKTEST_PERIOD = "3mo" 
BACKTEST_INTERVAL = "1h"
TRAIN_WINDOW = 1200
STEP_SIZE = 24
COST = 0.0001 # 1 pip round-trip (more realistic for institutional)

# Load XGB
XGB_MODEL_PATH = "xgb_breakout_filter.pkl"
xgb_model = joblib.load(XGB_MODEL_PATH) if os.path.exists(XGB_MODEL_PATH) else None

def run_audit():
    print(f"\n--- STARTING DEEP AUDIT FOR {AUDIT_TICKER} ---")
    data = fetch_data([AUDIT_TICKER], period=BACKTEST_PERIOD, interval=BACKTEST_INTERVAL)
    df = data[AUDIT_TICKER]
    macro_data = get_macro_data(interval=BACKTEST_INTERVAL, period=BACKTEST_PERIOD)
    
    df['Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['ATR'] = calculate_atr(df)
    df = df.dropna()
    
    total_bars = len(df)
    trades = []
    position = 0
    entry_price = None
    entry_sl = None
    entry_tp = None
    
    for t in range(TRAIN_WINDOW, total_bars, STEP_SIZE):
        train_slice = df.iloc[t - TRAIN_WINDOW:t].copy()
        regime, prob, direction, is_breakout, state_id, current_atr, kelly = detect_breakout(
            train_slice, ticker=AUDIT_TICKER, macro_data=macro_data
        )
        
        direction_hmm = 'LONG' if direction == 'LONG' else 'SHORT'
        mw = get_macro_weight(AUDIT_TICKER, direction_hmm, macro_data)
        adj_prob = prob * mw
        
        # LOG EVERY SCAN
        print(f"[{df.index[t]}] Regime: {regime:15} | Direction: {direction_hmm:7} | Prob: {prob:.2f} | Adj: {adj_prob:.2f}")
        
        # VETO AUDIT
        veto_reason = None
        if regime not in ['Trend Breakout', 'Mean Reversion']:
            veto_reason = "Consolidation"
        elif adj_prob < MAJORS_MIN_CONFIDENCE:
            veto_reason = f"Low Conf ({adj_prob:.2f})"
        elif xgb_model:
            xf = pd.DataFrame([{'state_id': state_id, 'hmm_confidence': prob, 'atr_normalized': current_atr/df['Close'].iloc[t]}])
            if xgb_model.predict(xf)[0] == 0:
                veto_reason = "XGBoost Veto"
        
        if veto_reason:
            print(f"   >>> VETO: {veto_reason}")
            desired = 0
        else:
            print(f"   >>> SIGNAL TRIGGERED! Kelly Size: {kelly:.1f}x")
            desired = 1 if direction_hmm == 'LONG' else -1
            
        # Run Simulation
        if position != 0:
            # Simple exit logic for audit
            for st in range(t, min(t + STEP_SIZE, total_bars)):
                price = df['Close'].iloc[st]
                # Check for exit (TP/SL) or Regime shift in next re-fit
                pass # Logic simplified for console logging

    print("\nAudit Complete.")

if __name__ == "__main__":
    run_audit()
