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

        # --- MAJORS SOPHISTICATION: Yield Curve Slope (2s10s) Filter ---
        if ticker in ["EURUSD=X", "GBPUSD=X"]:
            from config import FRED_2Y_TICKERS, FRED_TICKERS
            is_eur = ticker.startswith("EUR")
            ten_y_ticker = FRED_TICKERS.get('GER10Y' if is_eur else 'UK10Y')
            two_y_ticker = FRED_2Y_TICKERS.get('GER2Y' if is_eur else 'UK2Y')
            us_10y_ticker = "^TNX" 
            us_2y_ticker = FRED_2Y_TICKERS.get('US2Y')
            
            data_points = []
            for tkr in [ten_y_ticker, two_y_ticker, us_10y_ticker, us_2y_ticker]:
                df_tkr = macro_data.get(tkr)
                if df_tkr is not None and not df_tkr.empty:
                    slice_tkr = df_tkr[df_tkr.index <= current_time]
                    if not slice_tkr.empty:
                        data_points.append(slice_tkr['Close'].iloc[-1])
            
            if len(data_points) == 4:
                domestic_slope = data_points[0] - data_points[1]
                us_slope = data_points[2] - data_points[3]
                if (domestic_slope - us_slope) < -0.10: # Loosened from 0.20 to 10bps
                    return "BEARISH_ONLY"

        # --- MAJORS SOPHISTICATION: Basket Sync Filter ---
        if ticker in ["EURUSD=X", "GBPUSD=X"]:
            dxy_df = macro_data.get('DX-Y.NYB')
            if dxy_df is not None and not dxy_df.empty:
                dxy_slice = dxy_df[dxy_df.index <= current_time]
                if len(dxy_slice) >= 5:
                    dxy_mom = dxy_slice['Close'].iloc[-1] - dxy_slice['Close'].iloc[-5]
                    # EURUSD/GBPUSD Long needs Bearish USD (dxy_mom < 0)
                    if dxy_mom > 0.2: # Loosened from 0.4
                        return "BEARISH_ONLY" 
                    elif dxy_mom < -0.2: # Loosened from -0.4
                        return "BULLISH_ONLY" 

        # --- EFFICIENCY EQUILIBRIUM: Temporal Kill Zone Gate ---
        if ticker in ["EURUSD=X", "GBPUSD=X"]:
            from config import KILL_ZONES, LUNCH_ZONE
            hour = current_time.hour if hasattr(current_time, 'hour') else pd.to_datetime(current_time).hour
            
            in_kill_zone = any(start <= hour < end for start, end in KILL_ZONES)
            in_lunch = LUNCH_ZONE[0] <= hour < LUNCH_ZONE[1]
            
            if not in_kill_zone and not in_lunch:
                # Outside peak liquidity, veto new non-trend positions or force consolidation
                return "BEARISH_ONLY" # Arbitrary veto for technical breakouts in dead hours

            # Lunch Penalty: This will be handled in main.py/backtest.py by checking confidence

        # --- EFFICIENCY EQUILIBRIUM: Major Basket Sync ---
        if ticker in ["EURUSD=X", "GBPUSD=X"]:
            dxy_df = macro_data.get('DX-Y.NYB')
            other_major = "GBPUSD=X" if ticker == "EURUSD=X" else "EURUSD=X"
            other_df = macro_data.get(other_major)
            
            if dxy_df is not None and not dxy_df.empty and other_df is not None and not other_df.empty:
                dxy_slice = dxy_df[dxy_df.index <= current_time]
                other_slice = other_df[other_df.index <= current_time]
                
                if len(dxy_slice) >= 3 and len(other_slice) >= 3:
                    dxy_mom = dxy_slice['Close'].iloc[-1] - dxy_slice['Close'].iloc[-3]
                    other_mom = other_slice['Close'].iloc[-1] - other_slice['Close'].iloc[-3]
                    
                    # Logic: Before EURUSD Long, need Bearish DXY and Bullish GBP
                    # If DXY is rising, it's a "Liquidity Sweep" trap. Veto Longs.
                    if dxy_mom > 0.05:
                        return "BEARISH_ONLY" # Only allow shorts if DXY is rising
                    if other_mom < 0: # Lack of basket sync
                         return "BEARISH_ONLY" # Veto technical longs if others are weak

        # --- NEW GBP SOPHISTICATION: Gilt-Treasury Divergence ---
        if ticker == "GBPUSD=X":
            from config import FRED_TICKERS
            uk_10y = macro_data.get(FRED_TICKERS['UK10Y'])
            us_10y = macro_data.get('^TNX')
            if uk_10y is not None and us_10y is not None:
                uk_slice = uk_10y[uk_10y.index <= current_time]
                us_slice = us_10y[us_10y.index <= current_time]
                if len(uk_slice) >= 10 and len(us_slice) >= 10:
                    spread_curr = uk_slice['Close'].iloc[-1] - us_slice['Close'].iloc[-1]
                    spread_prev = uk_slice['Close'].iloc[-5] - us_slice['Close'].iloc[-5]
                    # If Gilt spread is narrowing, BoE is relatively more dovish than Fed -> Veto Longs
                    if spread_curr < spread_prev:
                        return "BEARISH_ONLY"
                    elif spread_curr > spread_prev:
                        return "BULLISH_ONLY"

        # --- NEW GOLD CONVERGENCE: Real Yield (TIPS) & DXY Gate ---
        if ticker == "GC=F":
            from config import TIPS_TICKER
            tips_df = macro_data.get(TIPS_TICKER)
            dxy_df = macro_data.get('DX-Y.NYB')
            
            if tips_df is not None and not tips_df.empty:
                tips_slice = tips_df[tips_df.index <= current_time]
                if len(tips_slice) >= 5:
                    tips_mom = tips_slice['Close'].iloc[-1] - tips_slice['Close'].iloc[-5]
                    # Rising Real Yields = Gold Death. Veto LONGs.
                    if tips_mom > 0.02:
                        return "BEARISH_ONLY"
            
            if dxy_df is not None and not dxy_df.empty:
                dxy_slice = dxy_df[dxy_df.index <= current_time]
                if len(dxy_slice) >= 5:
                    dxy_mom = dxy_slice['Close'].iloc[-1] - dxy_slice['Close'].iloc[-5]
                    # If DXY and Tips are both rising, Short Gold is only conviction
                    if dxy_mom > 0.2:
                        return "BEARISH_ONLY"

        # --- NEW OIL CONVERGENCE: Global Growth & USD Gate ---
        if ticker == "CL=F":
            from config import FRED_TICKERS
            dxy_df = macro_data.get('DX-Y.NYB')
            us_10y = macro_data.get('^TNX')
            us_2y = macro_data.get(FRED_2Y_TICKERS.get('US2Y'))
            
            if dxy_df is not None and not dxy_df.empty:
                dxy_slice = dxy_df[dxy_df.index <= current_time]
                if len(dxy_slice) >= 20:
                    # Multi-day DXY trend. If DXY is in a mega-rally (>1%), block Oil longs.
                    dxy_roc = (dxy_slice['Close'].iloc[-1] - dxy_slice['Close'].iloc[-20]) / dxy_slice['Close'].iloc[-20]
                    if dxy_roc > 0.01:
                        return "BEARISH_ONLY"

            # Growth Proxy: Yield Curve Slope (10Y-2Y). If inverted deeply, block longs (recession fears).
            if us_10y is not None and us_2y is not None:
                us_10_slice = us_10y[us_10y.index <= current_time]
                us_2_slice = us_2y[us_2y.index <= current_time]
                if len(us_10_slice) > 0 and len(us_2_slice) > 0:
                    slope = us_10_slice['Close'].iloc[-1] - us_2_slice['Close'].iloc[-1]
                    if slope < -0.30: # Hard inversion
                        return "BEARISH_ONLY"

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
