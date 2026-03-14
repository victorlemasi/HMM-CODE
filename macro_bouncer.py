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

        # --- GOLD OVERRIDE ---
        if ticker == "GC=F":
            if yield_df is not None and not yield_df.empty:
                yield_slice = yield_df[yield_df.index <= current_time]
                if len(yield_slice) >= 2:
                    current_yield = yield_slice['Close'].iloc[-1]
                    prev_yield = yield_slice['Close'].iloc[-2]
                    yield_change = current_yield - prev_yield
                    if current_dxy > 100.20 or yield_change > 0:
                        return "BEARISH_ONLY"

        # --- OIL OVERRIDE ---
        if ticker == "CL=F":
            if current_dxy > 100.50:
                return "SCALP_ONLY"

        # --- OIL-JPY CORRELATION FILTER ---
        if ticker.endswith("JPY=X"):
            oil_df_corr = macro_data.get('CL=F')
            if oil_df_corr is not None and not oil_df_corr.empty:
                oil_slice_corr = oil_df_corr[oil_df_corr.index <= current_time]
                if len(oil_slice_corr) >= 18:
                    oil_atr_series = calculate_atr(oil_slice_corr)
                    if len(oil_atr_series) >= 5:
                        current_oil_atr = oil_atr_series.iloc[-1]
                        prev_oil_atr = oil_atr_series.iloc[-5] 
                        if prev_oil_atr > 0:
                            atr_spike = (current_oil_atr - prev_oil_atr) / prev_oil_atr
                            if atr_spike > 0.02:
                                return "BULLISH_ONLY" # Blocks SHORT (Long JPY)

        # --- GENERAL MACRO DXY/OIL WALL ---
        if oil_df is not None and not oil_df.empty:
            oil_slice = oil_df[oil_df.index <= current_time]
            current_oil = oil_slice['Close'].iloc[-1]
            if current_dxy > DXY_WALL or current_oil > OIL_DANGER_ZONE:
                return "BEARISH_ONLY"

        if dxy_change > MOM_THRESHOLD:
            return "BEARISH_ONLY"

        if current_dxy > 98.50 and dxy_change > 0:
            return "BEARISH_ONLY"
            
        # --- RBNZ BIAS FILTER (Live Rates Automation) ---
        current_nz_yield = None
        # Priority: ^NZ10, Fallback: IRLTLT01NZM156N (FRED)
        nz_live = macro_data.get('^NZ10')
        if nz_live is not None:
            nz_slice = nz_live[nz_live.index <= current_time]
            if not nz_slice.empty: current_nz_yield = nz_slice['Close'].iloc[-1]
        
        if current_nz_yield is None:
            nz_fred = macro_data.get('IRLTLT01NZM156N')
            if nz_fred is not None:
                nz_slice = nz_fred[nz_fred.index <= current_time]
                if not nz_slice.empty: current_nz_yield = nz_slice['Close'].iloc[-1]

        if current_nz_yield is not None:
            if current_nz_yield > 3.0: # Hawkish
                if "NZD" in ticker:
                    if ticker.startswith("NZD"): return "BULLISH_ONLY"
                    else: return "BEARISH_ONLY"

        # --- GLOBAL YIELD SPREAD GATES (EURUSD, GBPUSD FIX) ---
        if ticker in ["EURUSD=X", "GBPUSD=X"]:
            base_key = 'IRLTLT01DEM156N' if "EUR" in ticker else 'IRLTLT01GBM156N'
            us_key = '^TNX'
            base_y = macro_data.get(base_key)
            us_y = macro_data.get(us_key)
            
            if base_y is not None and us_y is not None:
                b_slice = base_y[base_y.index <= current_time]
                u_slice = us_y[us_y.index <= current_time]
                if len(b_slice) >= 120 and len(u_slice) >= 120:
                    spread_curr = b_slice['Close'].iloc[-1] - u_slice['Close'].iloc[-1]
                    spread_prev = b_slice['Close'].iloc[-120] - u_slice['Close'].iloc[-120]
                    momentum = spread_curr - spread_prev
                    if momentum < -0.05: return "BEARISH_ONLY"
                    if momentum > 0.05: return "BULLISH_ONLY"

        return "ALLOW"
    except Exception:
        return "ALLOW"
def get_macro_weight(ticker: str, direction: str, macro_data: dict) -> float:
    """
    Returns a confidence weight (e.g., 1.2 or 0.8) based on Policy Rate differentials.
    """
    if macro_data is None or direction == "None":
        return 1.0
        
    from config import POLICY_RATE_TICKERS, ASSET_MAPPINGS, COMMODITY_TICKERS, YIELD_TICKERS
    
    if ticker not in ASSET_MAPPINGS:
        return 1.0
        
    mapping = ASSET_MAPPINGS[ticker]
    m_type = mapping['type']
    
    # --- TYPE 1: FX Macro (Policy Rate Differentials) ---
    if m_type == 'macro':
        base_currency = mapping['base_currency'] if 'base_currency' in mapping else ticker[:3]
        quote_currency = mapping['quote_currency'] if 'quote_currency' in mapping else ticker[3:6]
        
        base_rate_ticker = POLICY_RATE_TICKERS.get(base_currency)
        quote_rate_ticker = POLICY_RATE_TICKERS.get(quote_currency)
        
        if not base_rate_ticker or not quote_rate_ticker:
            return 1.0
            
        base_df = macro_data.get(base_rate_ticker)
        quote_df = macro_data.get(quote_rate_ticker)
        
        if base_df is None or quote_df is None or base_df.empty or quote_df.empty:
            return 1.0
            
        current_base = base_df['Close'].iloc[-1]
        current_quote = quote_df['Close'].iloc[-1]
        
        # Hawkish Base + Dovish Quote = Bullish for Pair
        if direction == "LONG":
            if current_base > current_quote: return 1.2
            elif current_base < current_quote: return 0.8
        elif direction == "SHORT":
            if current_base < current_quote: return 1.2
            elif current_base > current_quote: return 0.8
            
    # --- TYPE 2: Inverse Commodity (e.g., Oil vs DXY) ---
    elif m_type == 'commodity_inverse':
        dxy_df = macro_data.get('DX-Y.NYB')
        if dxy_df is not None and not dxy_df.empty:
            if len(dxy_df) >= 5:
                dxy_mom = dxy_df['Close'].iloc[-1] - dxy_df['Close'].iloc[-5]
                if direction == "LONG":
                    return 0.8 if dxy_mom > 0 else 1.2
                elif direction == "SHORT":
                    return 1.2 if dxy_mom > 0 else 0.8

    # --- TYPE 3: Direct Commodity (e.g., AUDUSD vs Copper) ---
    elif m_type == 'commodity':
        com_key = mapping['key']
        com_ticker = COMMODITY_TICKERS.get(com_key)
        com_df = macro_data.get(com_ticker)
        if com_df is not None and not com_df.empty:
            if len(com_df) >= 5:
                com_mom = com_df['Close'].iloc[-1] - com_df['Close'].iloc[-5]
                # Positive momentum in commodity is Bullish for the currency
                if direction == "LONG":
                    return 1.2 if com_mom > 0 else 0.8
                elif direction == "SHORT":
                    return 0.8 if com_mom > 0 else 1.2

    # --- TYPE 4: Pure Yield (e.g., USDJPY vs 10Y) ---
    elif m_type == 'yield':
        yield_key = mapping['key']
        yield_ticker = YIELD_TICKERS.get(yield_key)
        yield_df = macro_data.get(yield_ticker)
        if yield_df is not None and not yield_df.empty:
            if len(yield_df) >= 5:
                y_mom = yield_df['Close'].iloc[-1] - yield_df['Close'].iloc[-5]
                # Rising yield is Bullish for the currency
                if direction == "LONG":
                    return 1.2 if y_mom > 0 else 0.8
                elif direction == "SHORT":
                    return 0.8 if y_mom > 0 else 1.2

    return 1.0
