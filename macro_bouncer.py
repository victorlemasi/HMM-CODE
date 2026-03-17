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
        
        dxy_df = macro_data.get('DX-Y.NYB')
        oil_df = macro_data.get('BZ=F')
        yield_df = macro_data.get('^TNX')

        if dxy_df is None or dxy_df.empty:
            return "ALLOW"

        # Current values (last available before or at current_time)
        dxy_slice = dxy_df[dxy_df.index <= current_time]
        if len(dxy_slice) < 25: return "ALLOW"
        
        current_dxy = dxy_slice['Close'].iloc[-1]
        # Daily momentum (approx 24h/24 bars)
        dxy_change = (current_dxy - dxy_slice['Close'].iloc[-25]) / dxy_slice['Close'].iloc[-25]

        # --- NEW GENERIC MACRO: Yield Spread Momentum (Applicable to ALL Pairs) ---
        from config import ASSET_MAPPINGS, YIELD_TICKERS, FRED_TICKERS, POLICY_RATE_TICKERS
        if ticker in ASSET_MAPPINGS and ASSET_MAPPINGS[ticker]['type'] == 'macro':
            mapping = ASSET_MAPPINGS[ticker]
            base_y_tkr = YIELD_TICKERS.get(mapping['base']) or FRED_TICKERS.get(mapping['base'])
            quote_y_tkr = YIELD_TICKERS.get(mapping['quote']) or FRED_TICKERS.get(mapping['quote'])
            
            base_y_df = macro_data.get(base_y_tkr)
            quote_y_df = macro_data.get(quote_y_tkr)
            
            if base_y_df is not None and quote_y_df is not None:
                b_slice = base_y_df[base_y_df.index <= current_time]
                q_slice = quote_y_df[quote_y_df.index <= current_time]
                
                # Check 5-day / 120-bar momentum for yield spread
                lookback = 120 if len(b_slice) >= 120 else len(b_slice) // 2
                if lookback > 5:
                    spread_curr = b_slice['Close'].iloc[-1] - q_slice['Close'].iloc[-1]
                    spread_prev = b_slice['Close'].iloc[-lookback] - q_slice['Close'].iloc[-lookback]
                    momentum = spread_curr - spread_prev
                    
                    if momentum < -0.10: # Spread narrowing significantly
                        return "BEARISH_ONLY" if not ticker.startswith("USD") else "BULLISH_ONLY"
                    if momentum > 0.10: # Spread widening significantly
                        return "BULLISH_ONLY" if not ticker.startswith("USD") else "BEARISH_ONLY"

        # --- NEW GENERIC MACRO: Policy Rate Delta (Hikes/Cuts) ---
        if ticker in ASSET_MAPPINGS and ASSET_MAPPINGS[ticker]['type'] == 'macro':
            mapping = ASSET_MAPPINGS[ticker]
            for curr_key, side in [('base_currency', 'base'), ('quote_currency', 'quote')]:
                currency = mapping.get(curr_key)
                rate_tkr = POLICY_RATE_TICKERS.get(currency)
                rate_df = macro_data.get(rate_tkr)
                
                if rate_df is not None and not rate_df.empty:
                    r_slice = rate_df[rate_df.index <= current_time]
                    if len(r_slice) >= 5:
                        curr_rate = r_slice['Close'].iloc[-1]
                        prev_rate = r_slice['Close'].iloc[-5] # Catch recent shift (daily data usually)
                        
                        if curr_rate > prev_rate: # HAWKISH MOVE (Hike detected)
                            # If base hikes, buy pair. If quote hikes, sell pair.
                            return "BULLISH_ONLY" if side == 'base' else "BEARISH_ONLY"
                        elif curr_rate < prev_rate: # DOVISH MOVE (Cut detected)
                            return "BEARISH_ONLY" if side == 'base' else "BULLISH_ONLY"


        return "ALLOW"
    except Exception:
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
