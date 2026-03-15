
import pandas as pd
import numpy as np
from hmm_analysis import detect_breakout, get_dynamic_exit_levels
from data_fetcher import get_macro_data, fetch_data
from macro_bouncer import check_fundamental_gatekeeper, get_macro_weight
from config import ATR_MULTIPLIER_FX, ATR_MULTIPLIER_GOLD, PERIOD, INTERVAL

def diagnostic_backtest(ticker):
    print(f"\n--- Diagnostic Backtest for {ticker} ---")
    macro_data = get_macro_data(INTERVAL, PERIOD)
    data = fetch_data([ticker], INTERVAL, PERIOD)
    if not data: return
    df = data[ticker]
    
    TRAIN_WINDOW = 1200
    STEP_SIZE = 24
    total_bars = len(df)
    
    for t in range(TRAIN_WINDOW, total_bars, STEP_SIZE):
        train_slice = df.iloc[t - TRAIN_WINDOW:t].copy()
        current_time = df.index[t]
        
        try:
            is_breakout, direction, regime, _, current_atr, prob = detect_breakout(train_slice, ticker=ticker, macro_data=macro_data)
        except Exception as e:
            print(f"[{current_time}] Error: {e}")
            continue
            
        if regime in ['Trend Breakout', 'Mean Reversion']:
            # Macro Weighting
            macro_w = get_macro_weight(ticker, direction, macro_data)
            adj_prob = prob * macro_w
            
            # Confidence Check
            if adj_prob < 0.6:
                print(f"[{current_time}] VETO: Low Confidence ({adj_prob:.2f} | Raw: {prob:.2f} | Weight: {macro_w:.2f})")
                continue
                
            # Bouncer Check
            macro_status = check_fundamental_gatekeeper(ticker, current_time, macro_data)
            if macro_status == "BEARISH_ONLY" and direction == "LONG":
                print(f"[{current_time}] VETO: Macro Bouncer (Bearish Bias vs {direction})")
                continue
            elif macro_status == "BULLISH_ONLY" and direction == "SHORT":
                print(f"[{current_time}] VETO: Macro Bouncer (Bullish Bias vs {direction})")
                continue
            
            print(f"[{current_time}] SIGNAL: {direction} in {regime} (Prob: {adj_prob:.2f}) - PASSED")
        else:
            # Check if it was rejected by the separation guard INSIDE detect_breakout
            pass

if __name__ == "__main__":
    for ticker in ['NZDJPY=X', 'GC=F']:
        diagnostic_backtest(ticker)
