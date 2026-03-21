
import pandas as pd
import numpy as np
import pickle
import os
from data_fetcher import fetch_data, get_macro_data
from hmm_analysis import detect_breakout

def run_debug():
    from config import HMM_MODELS_PATH
    for symbol in ["USDJPY=X", "GC=F"]:
        print(f"\n--- Debugging {symbol} ---")
        try:
            df = fetch_data(symbol, period="70d", interval="1h")
            macro_data = get_macro_data(period="70d", interval="1h")
            
            model_name = symbol.replace('=X', '').replace('=F', '')
            model_file = os.path.join(HMM_MODELS_PATH, f"{model_name}_hmm.pkl")
            
            pretrained = None
            if os.path.exists(model_file):
                with open(model_file, 'rb') as f:
                    pretrained = pickle.load(f)
                print(f"      Loaded model from {model_file}")
            
            is_breakout, direction, regime, state_id, atr, prob = detect_breakout(df, ticker=symbol, macro_data=macro_data, model=pretrained)
            print(f"      Regime: {regime} | Direction: {direction} | Prob: {prob:.4f}")
            
            # Check Thresholds
            from config import MAJORS_MIN_CONFIDENCE, MINORS_MIN_CONFIDENCE, MAJORS_FIX_LIST
            is_major = symbol in MAJORS_FIX_LIST
            thresh = MAJORS_MIN_CONFIDENCE if is_major else MINORS_MIN_CONFIDENCE
            print(f"      Active Threshold: {thresh:.2f} | Pass: {prob >= thresh}")
            
        except Exception as e:
            print(f"      [DEBUG ERROR] {symbol}: {e}")

if __name__ == "__main__":
    run_debug()
