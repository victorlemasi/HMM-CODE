"""
Per-bar diagnostic: traces exactly what prob/regime/macro_bias EURUSD produces
for ONE walk-forward step so we understand why trades are filtered.
"""
import sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

sys.path.insert(0, r"c:\Users\lenovo\Downloads\scanner\Currency-Pair-Scanner-Analysis")

from data_fetcher import fetch_data, get_macro_data
from hmm_analysis import detect_breakout, calculate_atr
from macro_bouncer import check_fundamental_gatekeeper, get_macro_weight
from config import MAJORS_MIN_CONFIDENCE, MAJORS_FIX_LIST, LUNCH_ZONE

TRAIN_WINDOW = 1200

df_all = fetch_data(['EURUSD=X'], period='6mo', interval='1h').get('EURUSD=X')
macro  = get_macro_data(interval='1h', period='6mo')

df_all['Returns'] = np.log(df_all['Close'] / df_all['Close'].shift(1))
df_all['ATR']     = calculate_atr(df_all)
df_all = df_all.dropna()

# Pick t = TRAIN_WINDOW (first valid step)
t = TRAIN_WINDOW
train_slice = df_all.iloc[t - TRAIN_WINDOW:t].copy()

print(f"Training on bars [{t-TRAIN_WINDOW}:{t}] ({len(train_slice)} bars)")

try:
    is_bo, direction, regime, _, current_atr, prob = detect_breakout(
        train_slice, ticker='EURUSD=X', macro_data=macro, model=None
    )
    print(f"\n✓ detect_breakout OK")
    print(f"  regime={regime}, direction={direction}, prob={prob:.4f}, is_breakout={is_bo}")
    print(f"  ATR={current_atr:.6f}")

    direction_hmm = 'LONG' if direction == 'LONG' else 'SHORT'
    macro_weight   = get_macro_weight('EURUSD=X', direction_hmm, macro)
    adjusted_prob  = prob * macro_weight
    print(f"\n  prob={prob:.4f} × macro_weight={macro_weight:.4f} = adjusted={adjusted_prob:.4f}")
    print(f"  MAJORS_MIN_CONFIDENCE = {MAJORS_MIN_CONFIDENCE}")

    hour = df_all.index[t].hour
    is_lunch = LUNCH_ZONE[0] <= hour < LUNCH_ZONE[1]
    conf_thresh = 0.90 if is_lunch else MAJORS_MIN_CONFIDENCE
    print(f"  hour={hour}, is_lunch={is_lunch}, conf_thresh={conf_thresh}")
    print(f"  Passes threshold? {adjusted_prob >= conf_thresh}")

    if adjusted_prob >= conf_thresh:
        macro_bias = check_fundamental_gatekeeper('EURUSD=X', df_all.index[t], macro)
        print(f"\n  macro_bias = {macro_bias}")
        is_veto = ("BEARISH" in macro_bias and direction_hmm == "LONG") or \
                  ("BULLISH" in macro_bias and direction_hmm == "SHORT")
        print(f"  is_veto = {is_veto}")

except Exception as e:
    import traceback
    print(f"\n✗ EXCEPTION: {type(e).__name__}: {e}")
    traceback.print_exc()
