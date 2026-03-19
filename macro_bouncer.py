import pandas as pd
import numpy as np
from hmm_analysis import calculate_atr

def check_fundamental_gatekeeper(ticker: str, current_time, macro_data: dict):
    """
    Consolidated Hybrid Bouncer (Thresholds + Momentum + Yields).
    Used by both main.py (Live) and backtest.py (Historical).
    """
    if macro_data is None:
        return "ALLOW"

    try:
        # Thresholds (War-Time March 2026 calibrated)
        DXY_WALL = 100.40
        OIL_DANGER_ZONE = 98.00 
        MOM_THRESHOLD = 0.0025
        
        # --- THE MACRO REALITY: 2s10s Steepening Trap ---
        # If the 2Y is dropping much faster than the 10Y while still inverted, 
        # it's a classic "Bull-Steepener" signaling a hard landing.
        us10_df = macro_data.get('DGS10')  # US 10Y
        us2_df = macro_data.get('GS2')     # US 2Y
        
        is_bull_steepener = False
        if us10_df is not None and us2_df is not None and not us10_df.empty and not us2_df.empty:
            # Sync indexes
            u10 = us10_df.copy()
            u2 = us2_df.copy()
            if u10.index.tzinfo is None: u10.index = u10.index.tz_localize('UTC')
            if u2.index.tzinfo is None: u2.index = u2.index.tz_localize('UTC')
            
            curve_df = pd.DataFrame({'US10': u10['Close'], 'US2': u2['Close']}).sort_index().ffill().dropna()
            curve_df = curve_df[curve_df.index <= pd.to_datetime(current_time, utc=True)]
            
            if len(curve_df) >= 20: # Ensure enough history
                recent_spread = curve_df['US10'].iloc[-1] - curve_df['US2'].iloc[-1]
                past_spread = curve_df['US10'].iloc[-20] - curve_df['US2'].iloc[-20]
                
                # Inverted (10Y < 2Y) AND Steepening (spread becoming less negative)
                is_inverted = recent_spread < 0
                is_steepening = (recent_spread - past_spread) > 0.05 # 5 bps steepening over window
                
                if is_inverted and is_steepening:
                    is_bull_steepener = True
                    print(f"  [MACRO ALERT] US 2s10s Bull-Steepener Detected! (Spread: {recent_spread:.2f}%)")
                    
        # Apply the steepener veto
        if is_bull_steepener:
            # Toxic to be Long USD here.
            # If USD is Quote (EURUSD, GBPUSD), we only allow BULLISH trades (Long EUR, Short USD)
            if ticker in ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "NZDUSD=X", "GC=F"]:
                biases.append("BULLISH_ONLY")
            # If USD is Base (USDJPY, USDCHF, USDCAD), we only allow BEARISH trades (Short USD, Long JPY)
            elif ticker in ["USDJPY=X", "USDCHF=X", "USDCAD=X"]:
                biases.append("BEARISH_ONLY")
                
        DXY_WALL = 100.40
        OIL_DANGER_ZONE = 98.00 
        MOM_THRESHOLD = 0.0025
        
        # Ensure current_time is a UTC-aware Timestamp
        current_time = pd.to_datetime(current_time)
        if current_time.tzinfo is None:
            current_time = current_time.tz_localize('UTC')
        else:
            current_time = current_time.tz_convert('UTC')

        dxy_df = macro_data.get('DX-Y.NYB')
        
        if dxy_df is not None and not dxy_df.empty:
            # Ensure index is UTC-aware for comparison
            if dxy_df.index.tzinfo is None:
                dxy_df.index = dxy_df.index.tz_localize('UTC')
            
            dxy_slice = dxy_df[dxy_df.index <= current_time]
            if len(dxy_slice) >= 25:
                current_dxy = dxy_slice['Close'].iloc[-1]
                dxy_change = (current_dxy - dxy_slice['Close'].iloc[-25]) / dxy_slice['Close'].iloc[-25]

        biases = []
        
        # --- NEW GENERIC MACRO: Yield Spread Momentum (Applicable to ALL Pairs) ---
        from config import ASSET_MAPPINGS, YIELD_TICKERS, FRED_TICKERS
        if ticker in ASSET_MAPPINGS and ASSET_MAPPINGS[ticker]['type'] == 'macro':
            mapping = ASSET_MAPPINGS[ticker]
            base_y_tkr = YIELD_TICKERS.get(mapping['base']) or FRED_TICKERS.get(mapping['base'])
            quote_y_tkr = YIELD_TICKERS.get(mapping['quote']) or FRED_TICKERS.get(mapping['quote'])
            
            base_y_df = macro_data.get(base_y_tkr)
            quote_y_df = macro_data.get(quote_y_tkr)
            
            if base_y_df is not None and quote_y_df is not None and not base_y_df.empty and not quote_y_df.empty:
                # Ensure indices are UTC-aware before aligning
                b_df = base_y_df.copy()
                q_df = quote_y_df.copy()
                if b_df.index.tzinfo is None: b_df.index = b_df.index.tz_localize('UTC')
                else: b_df.index = b_df.index.tz_convert('UTC')
                if q_df.index.tzinfo is None: q_df.index = q_df.index.tz_localize('UTC')
                else: q_df.index = q_df.index.tz_convert('UTC')

                # Align indices to handle mixed frequencies (e.g. Daily vs Monthly)
                combined = pd.DataFrame({
                    'base': b_df['Close'],
                    'quote': q_df['Close']
                }).sort_index().ffill().dropna()
                
                # Filter up to current_time
                combined = combined[combined.index <= current_time]
                
                if len(combined) >= 50:
                    # Lookback for momentum: 240 bars (~10 trading days for hourly data)
                    lb = min(len(combined) - 1, 240)
                    
                    spread = combined['base'] - combined['quote']
                    momentum = spread.iloc[-1] - spread.iloc[-lb]
                    
                    from config import YIELD_THRESHOLD
                    # Use synced config threshold
                    if momentum < -YIELD_THRESHOLD: 
                        biases.append("BEARISH_ONLY")
                    elif momentum > YIELD_THRESHOLD:
                        biases.append("BULLISH_ONLY")
                    else:
                        biases.append("NEUTRAL")

        # --- POLICY RATE COMPARISON (live FRED data, gracefully skips if unavailable) ---
        from config import ASSET_MAPPINGS as _AM, POLICY_RATE_TICKERS
        if ticker in _AM and _AM[ticker]['type'] == 'macro':
            mapping = _AM[ticker]
            base_curr = mapping.get('base_currency')
            quote_curr = mapping.get('quote_currency')
            base_rate_tkr = POLICY_RATE_TICKERS.get(base_curr)
            quote_rate_tkr = POLICY_RATE_TICKERS.get(quote_curr)

            base_r_df = macro_data.get(base_rate_tkr) if base_rate_tkr else None
            quote_r_df = macro_data.get(quote_rate_tkr) if quote_rate_tkr else None

            base_rate = None
            quote_rate = None

            if base_r_df is not None and not base_r_df.empty:
                if base_r_df.index.tzinfo is None:
                    base_r_df.index = base_r_df.index.tz_localize('UTC')
                b_slice = base_r_df[base_r_df.index <= current_time]
                if not b_slice.empty:
                    base_rate = b_slice['Close'].iloc[-1]

            if quote_r_df is not None and not quote_r_df.empty:
                if quote_r_df.index.tzinfo is None:
                    quote_r_df.index = quote_r_df.index.tz_localize('UTC')
                q_slice = quote_r_df[quote_r_df.index <= current_time]
                if not q_slice.empty:
                    quote_rate = q_slice['Close'].iloc[-1]

            if base_rate is not None and quote_rate is not None:
                diff = base_rate - quote_rate
                if diff > 1.5:
                    biases.append("BULLISH_ONLY")
                elif diff < -1.5:
                    biases.append("BEARISH_ONLY")
                else:
                    biases.append("NEUTRAL")

        # Filter out NEUTRAL from the display biases to keep it clean (Macro Gatekeeper: BEARISH_ONLY style)
        active_biases = [b for b in biases if "NEUTRAL" not in b]
        
        return " | ".join(active_biases) if active_biases else "ALLOW"

    except Exception as e:
        print(f"  [MACRO ERROR] {ticker}: {e}")
        return "ALLOW"
def get_macro_weight(ticker: str, direction: str, macro_data: dict) -> float:
    """
    Returns a confidence multiplier based on Policy Rate differentials and MOMENTUM.
    Formula: (1 + Differential_Score) where Score considers both levels and hawks/doves direction.
    """
    if macro_data is None or direction in ["None", "⚠️LONG", "⚠️SHORT"]:
        return 1.0
        
    from config import POLICY_RATE_TICKERS, ASSET_MAPPINGS
    
    if ticker not in ASSET_MAPPINGS:
        return 1.0
        
    mapping = ASSET_MAPPINGS[ticker]
    m_type = mapping['type']
    score = 0.0
    
    # --- TYPE 1: FX Macro (Policy Rate Levels + Momentum) ---
    if m_type == 'macro':
        base_currency = mapping.get('base_currency', ticker[:3])
        quote_currency = mapping.get('quote_currency', ticker[3:6])
        
        base_rate_ticker = POLICY_RATE_TICKERS.get(base_currency)
        quote_rate_ticker = POLICY_RATE_TICKERS.get(quote_currency)
        
        if base_rate_ticker and quote_rate_ticker:
            base_df = macro_data.get(base_rate_ticker)
            quote_df = macro_data.get(quote_rate_ticker)
            
            if base_df is not None and quote_df is not None and not base_df.empty and not quote_df.empty:
                # 1. Current Levels (Carry Advantage)
                curr_base = base_df['Close'].iloc[-1]
                curr_quote = quote_df['Close'].iloc[-1]
                diff_factor = 0.1 if curr_base > curr_quote else (-0.1 if curr_base < curr_quote else 0.0)
                
                # 2. Rate Momentum (Hawkish/Dovish Shift - 24 bar window)
                base_lookback = base_df['Close'].iloc[-24] if len(base_df) >= 24 else base_df['Close'].iloc[0]
                quote_lookback = quote_df['Close'].iloc[-24] if len(quote_df) >= 24 else quote_df['Close'].iloc[0]
                
                base_mom = 0.1 if curr_base > base_lookback else (-0.1 if curr_base < base_lookback else 0.0)
                quote_mom = 0.1 if curr_quote > quote_lookback else (-0.1 if curr_quote < quote_lookback else 0.0)
                
                # Total Score: (+) favors base currency (Pair Long), (-) favors quote
                score = diff_factor + base_mom - quote_mom
                
                return 1.0 + (score if direction == "LONG" else -score)
            
    # --- TYPE 2: Inverse Commodity (e.g., Oil vs DXY Momentum) ---
    elif m_type == 'commodity_inverse':
        dxy_df = macro_data.get('DX-Y.NYB')
        if dxy_df is not None and not dxy_df.empty and len(dxy_df) >= 5:
            dxy_mom = dxy_df['Close'].iloc[-1] - dxy_df['Close'].iloc[-5]
            # Strengthening DXY (mom > 0) is Bearish for Oil
            # If DXY up, Score is -0.15 for Long, +0.15 for Short
            score = -0.15 if dxy_mom > 0 else 0.15
            return 1.0 + (score if direction == "LONG" else -score)

    return 1.0
