import pandas as pd
import time
import json
import os
import sys
from datetime import datetime, timedelta

# Fix Windows console encoding for emoji/unicode in direction strings
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from data_fetcher import fetch_data, get_returns_matrix, get_macro_data, fetch_watchdog_data
from clustering import cluster_assets, plot_clusters
from hmm_analysis import detect_breakout, get_dynamic_exit_levels, get_trigger_price, calculate_z_score
from config import (
    CURRENCY_PAIRS, INTERVAL, PERIOD, N_CLUSTERS, GPR_SPIKE_THRESHOLD, 
    SAFE_HAVEN_TICKER, MAJORS_FIX_LIST, MAJORS_MACRO_ENABLE, 
    ASSET_MAPPINGS, YIELD_TICKERS, FRED_TICKERS, YIELD_THRESHOLD, CONFIRMATION_BUFFER, MAJORS_TP_MULTIPLIER,
    WATCHDOG_TICKERS
)
from gpr_fetcher import fetch_latest_gpr

from sentiment_fetcher import fetch_market_sentiment
from rebalancer import diversify_signals, find_correlation_hedges, get_exit_recommendations
from macro_bouncer import check_fundamental_gatekeeper, get_macro_weight

TRACKER_FILE = 'trade_tracker.json'

def load_tracker():
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_tracker(data):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=4)

class JumpWatchdog:
    def __init__(self, tickers):
        self.tickers = tickers
        self.paused_until = None
        
    def check_for_jumps(self):
        if self.paused_until and datetime.now() < self.paused_until:
            return True
            
        from config import WATCHDOG_JUMP_THRESHOLDS
        from hmm_analysis import calculate_mahalanobis_distance
        print("\n--- Running 1-Minute Jump Watchdog ---")
        wd_data = fetch_watchdog_data(self.tickers)
        for ticker, df in wd_data.items():
            if ticker == "GC=F":
                # Use multi-dim distance for Gold (Price + Vol)
                score = calculate_mahalanobis_distance(df)
            else:
                score = calculate_z_score(df['Close'])
                
            # Use specific threshold or fallback to DEFAULT
            threshold = WATCHDOG_JUMP_THRESHOLDS.get(ticker, WATCHDOG_JUMP_THRESHOLDS['DEFAULT'])
            
            if abs(score) > threshold:
                metric_name = "Mahalanobis" if ticker == "GC=F" else "Z-Score"
                print(f"!!! JUMP DETECTED on {ticker} ({metric_name}: {score:.2f} | Limit: {threshold}) !!!")
                print("ACTION: Pausing all trading operations for 15 minutes.")
                self.paused_until = datetime.now() + timedelta(minutes=15)
                return True
        return False

def get_yield_spread_momentum(ticker, macro_data):
    """
    Calculates the 5-bar trend of the yield spread.
    Positive means Base Yield is rising faster than Quote Yield.
    """
    if ticker not in ASSET_MAPPINGS or ASSET_MAPPINGS[ticker]['type'] != 'macro':
        return 0
        
    mapping = ASSET_MAPPINGS[ticker]
    base_ticker = YIELD_TICKERS.get(mapping['base']) or FRED_TICKERS.get(mapping['base'])
    quote_ticker = YIELD_TICKERS.get(mapping['quote']) or FRED_TICKERS.get(mapping['quote'])
    
    if base_ticker not in macro_data or quote_ticker not in macro_data or macro_data[base_ticker].empty or macro_data[quote_ticker].empty:
        # Fallback to DXY momentum for USD pairs if specific yields are missing
        if "USD" in ticker:
            dxy_ticker = 'DX-Y.NYB'
            if dxy_ticker in macro_data and not macro_data[dxy_ticker].empty:
                dxy_df = macro_data[dxy_ticker]
                if len(dxy_df) >= 6:
                    # If DXY is rising, USD is strengthening -> Negative momentum for EURUSD/GBPUSD
                    momentum = dxy_df['Close'].iloc[-1] - dxy_df['Close'].iloc[-5]
                    # If USD is base (USDJPY, USDCHF, USDCAD), DXY up is positive momentum
                    return momentum if ticker.startswith("USD") else -momentum
        return 0
        
    base_df = macro_data[base_ticker]
    quote_df = macro_data[quote_ticker]
    
    # Align indices to handle mixed frequencies (Daily vs Monthly)
    # Note: macro_data from get_macro_data() already contains pandas DataFrames
    combined = pd.DataFrame({
        'base': base_df['Close'],
        'quote': quote_df['Close']
    }).sort_index().ffill().dropna()
    
    if len(combined) < 20:
        return 0
        
    lb = min(len(combined) - 1, 240) # ~10 trading days
    spread = combined['base'] - combined['quote']
    momentum = spread.iloc[-1] - spread.iloc[-lb]
    return momentum

def check_macro_alignment(ticker, direction, macro_data):
    """
    Determines if the macro trend supports the technical breakout.
    """
    from config import ASSET_MAPPINGS
    if not MAJORS_MACRO_ENABLE or ticker not in ASSET_MAPPINGS or ASSET_MAPPINGS[ticker]['type'] != 'macro':
        return "WIN_PHASE" # Allow if macro is disabled or not a macro asset
        
    momentum = get_yield_spread_momentum(ticker, macro_data)
    
    # Threshold check
    if abs(momentum) < YIELD_THRESHOLD:
        return "TRAP_PHASE"
        
    if direction == "LONG" and momentum > 0:
        return "WIN_PHASE"
    elif direction == "SHORT" and momentum < 0:
        return "WIN_PHASE"
        
    return "TRAP_PHASE"


def main():
    watchdog = JumpWatchdog(WATCHDOG_TICKERS)
    tracked_trades = load_tracker()
    new_tracker = {} # Refresh to only keep active trades
    
    # 0. Global Sentiment Assessment
    print("\n--- Market Sentiment & Risk Assessment ---")
    gpr_val, is_gpr_spike, gpr_msg = fetch_latest_gpr(threshold_std=GPR_SPIKE_THRESHOLD)
    print(gpr_msg)
    
    sent_val, sent_class, sent_recom = fetch_market_sentiment()
    print(f"Market Sentiment: {sent_val} ({sent_class}) -> RECOMMENDATION: {sent_recom}")
    
    # 1. Fetch data
    print("\n=== Currency Pair Analysis Pipeline ===")
    
    # --- JUMP WATCHDOG CHECK ---
    if watchdog.check_for_jumps():
        print("Trading paused due to market shock. Skipping analysis.")
        return

    data = fetch_data(CURRENCY_PAIRS, INTERVAL, PERIOD)
    
    if not data:
        print("No data fetched. Exiting.")
        return
        
    print("\n--- Fetching Macro Context (Yields/Commodities/Rates) ---")
    macro_data = get_macro_data(INTERVAL, PERIOD)
    
    # 2. Clustering Analysis (Optimized via Silhouette)
    print("\n--- Running Clustering Analysis ---")
    returns_df = pd.DataFrame({p: df['Returns'] for p, df in data.items()}).dropna()
    cluster_mapping, correlation_matrix = cluster_assets(returns_df)
    plot_clusters(correlation_matrix, cluster_mapping)
    print("Clustering complete. Result saved to 'correlation_clusters.png'.")
    
    # 3. HMM Breakout Analysis (Enhanced with BIC and RSI)
    print("\n--- Running HMM Regime Detection ---")
    regime_results = {}
    breakout_directions = {}
    warnings_dict = {}
    macro_statuses = {}
    
    for pair, df in data.items():
        try:
            pair_warnings = []
            if is_gpr_spike and pair == SAFE_HAVEN_TICKER:
                pair_warnings.append("GPR Spike -> Safe Haven Priority")
                
            is_breakout, direction, regime, _, current_atr, prob = detect_breakout(df, ticker=pair, macro_data=macro_data)
            
            # --- APPLY THE FUNDAMENTAL BOUNCER (Global Gatekeeper) ---
            current_time = df.index[-1]
            gatekeeper_status = check_fundamental_gatekeeper(pair, current_time, macro_data)
            
            if gatekeeper_status != "ALLOW":
                pair_warnings.append(f"Macro Gatekeeper: {gatekeeper_status}")
            macro_statuses[pair] = gatekeeper_status
                
            
            # Calculate Dynamic Exit Levels
            current_price = df['Close'].iloc[-1]
            is_scalp = (pair == "CL=F" and gatekeeper_status == "SCALP_ONLY")
            tp, sl = get_dynamic_exit_levels(regime, current_price, current_atr, direction, ticker=pair, is_scalp=is_scalp)
            
            if is_scalp:
                print(f"  {pair} | SCALP MODE: Applied 1:1 ATR targets.")
            
            # Calculate 1.2 Candle Trigger for All Macro Pairs
            trigger = None
            macro_phase = "WIN_PHASE" # Default to allow for non-macro assets
            
            from config import ASSET_MAPPINGS
            is_macro_asset = pair in ASSET_MAPPINGS and ASSET_MAPPINGS[pair]['type'] == 'macro'
            
            if is_macro_asset and regime == "Trend Breakout":
                macro_phase = check_macro_alignment(pair, direction, macro_data)
            
            # --- MACRO WEIGHTING (Applied AFTER gatekeeper) ---
            macro_weight = get_macro_weight(pair, direction, macro_data)
            adjusted_prob = prob * macro_weight
            
            if ("BEARISH" in gatekeeper_status) and direction == "LONG":
                print(f"  [VETO] {pair} LONG signal rejected: Macro Bias ({gatekeeper_status}).")
                direction = "⚠️LONG"
            elif ("BULLISH" in gatekeeper_status) and direction == "SHORT":
                print(f"  [VETO] {pair} SHORT signal rejected: Macro Bias ({gatekeeper_status}).")
                direction = "⚠️SHORT"
            elif gatekeeper_status == "SCALP_ONLY" and pair == "CL=F":
                # Print notice but logic is handled above in TP/SL calculation
                pass
            
            # --- EFFICIENCY EQUILIBRIUM: Confidence Thresholds ---
            from config import MAJORS_MIN_CONFIDENCE, EURUSD_FIX_LIST, LUNCH_ZONE
            conf_thresh = MAJORS_MIN_CONFIDENCE if pair in MAJORS_FIX_LIST else 0.7
            
            # London Lunch Penalty
            hour_utc = current_time.hour
            if pair in MAJORS_FIX_LIST and LUNCH_ZONE[0] <= hour_utc < LUNCH_ZONE[1]:
                conf_thresh = 0.90
                pair_warnings.append("LUNCH ZONE Penalty")
                print(f"  {pair} | LUNCH ZONE: Increasing confidence threshold to 0.90")

            if adjusted_prob < conf_thresh and direction not in ["None", "⚠️LONG", "⚠️SHORT"]:
                 print(f"  [VETO] {pair} Signal Rejected: Low Contextual Confidence ({adjusted_prob:.2f} < {conf_thresh})")
                 pair_warnings.append(f"Low Confidence ({adjusted_prob:.2f} < {conf_thresh})")
                 direction = f"⚠️{direction}"

            # Calculate 1.2 Candle Trigger
            trigger = None
            if regime == "Trend Breakout" and direction not in ["None", "⚠️LONG", "⚠️SHORT"]:
                # Majors always use 1.2 logic; others use it if in a macro-supported phase
                trigger = get_trigger_price(df, regime, direction, current_atr, macro_phase=macro_phase)
            
            # breakout_directions[pair] assignment moved to end of loop
            
            # Re-format warnings to include Macro Gatekeeper prefix if not already present
            final_warnings = pair_warnings
            warnings_dict[pair] = " | ".join(final_warnings) if final_warnings else ""
            
            
            # --- TRACKING LOGIC ---
            if direction in ["LONG", "SHORT"]:
                # If already tracked, carry over entry time
                if pair in tracked_trades and tracked_trades[pair]['dir'] == direction:
                    new_tracker[pair] = tracked_trades[pair]
                    new_tracker[pair]['bars_active'] = tracked_trades.get(pair, {}).get('bars_active', 0) + 1
                    
                    # --- SIGNAL EXPIRY (Differentiated: 3 bars FX / 2 bars Commodities) ---
                    expiry_limit = 3 if pair.endswith("=X") else 2
                    if new_tracker[pair]['bars_active'] >= expiry_limit:
                        print(f"  [SIGNAL EXPIRED] {pair} failed to trigger within {expiry_limit} bars.")
                        direction = "None"
                        regime = "Consolidation" # Reset regime on expiry for consistency
                        del new_tracker[pair]
                    
                    # --- EFFICIENCY EQUILIBRIUM: Progressive SAR-style Stops ---
                    if pair in EURUSD_FIX_LIST and direction != "None": # Only apply if signal is still active
                        pnl_atr = (current_price - new_tracker[pair]['entry']) / current_atr if direction == "LONG" else (new_tracker[pair]['entry'] - current_price) / current_atr
                        if pnl_atr > 0.5:
                            # Tighten SL as price moves
                            trail_move = pnl_atr * 0.5 * current_atr
                            new_sl = new_tracker[pair]['entry'] + trail_move if direction == "LONG" else new_tracker[pair]['entry'] - trail_move
                            # Only tighten, never loosen
                            if direction == "LONG":
                                new_tracker[pair]['sl'] = max(new_tracker[pair].get('sl', 0), new_sl)
                            else:
                                new_tracker[pair]['sl'] = min(new_tracker[pair].get('sl', 999999), new_sl)
                            print(f"  {pair} | PROGRESSIVE STOP: Tightened SL to {new_tracker[pair]['sl']:.5f} (PnL: {pnl_atr:.2f} ATR)")
                else:
                    # New Entry
                    new_tracker[pair] = {
                        'dir': direction,
                        'entry_time': datetime.now().isoformat(),
                        'regime': regime,
                        'bars_active': 0
                    }
            
            # Diagnostic: show current state
            msg = f"  {pair:<12} | Regime: {regime:<15} | Dir: {direction} | Conf: {adjusted_prob:.2f}"
            if pair in MAJORS_FIX_LIST and regime == "Trend Breakout":
                msg += f" | Macro: {macro_phase}"
            if tp and sl:
                msg += f" | TP: {tp:.5f} | SL: {sl:.5f}"
            if trigger:
                msg += f" | TRIGGER: {trigger:.5f}"
            print(msg)

            # --- FINAL STATE UPDATE (Ensure CSV matches Terminal) ---
            regime_results[pair] = regime
            breakout_directions[pair] = direction
            warnings_dict[pair] = " | ".join(pair_warnings) if pair_warnings else ""

        except Exception as e:
            print(f"Error analyzing {pair}: {e}")
            regime_results[pair] = "Error"
            breakout_directions[pair] = "None"
    
    # 4. Final Summary
    print("\n=== Summary Report ===")
    
    # DEBUG: Check for mismatch in labels
    ticker_set = set(returns_df.columns)
    loop_set = set(regime_results.keys())
    if ticker_set != loop_set:
        print(f"!!! INDEX MISMATCH: returns_df has {len(ticker_set)} cols, but loop processed {len(loop_set)} pairs.")
        print(f"  Missing from returns_df: {loop_set - ticker_set}")
        print(f"  Extra in returns_df: {ticker_set - loop_set}")
        
    # Force summary index to be all analyzed pairs for total alignment
    summary = pd.DataFrame(index=list(regime_results.keys()))
    summary['Cluster'] = pd.Series(cluster_mapping) # Align as Series
    summary['Regime'] = pd.Series(regime_results)
    summary['Direction'] = pd.Series(breakout_directions)
    summary['State'] = summary['Regime'] # For compatibility with rebalancer
    summary['Warnings'] = pd.Series(warnings_dict)
    
    # Risk Overlay
    print("\n--- Risk Overlay ---")
    if is_gpr_spike:
        print("!!! WARNING: GEOPOLITICAL RISK SPIKING !!!")
        print("ACTION: Switching to SAFE HAVEN mode.")
        print(f"FOCUS: Prioritize {SAFE_HAVEN_TICKER} (Gold) signals.")
    
    if "Caution" in sent_recom:
        print(f"ALERT: Sentiment {sent_class} suggests cautious positioning.")

    # Diversification & Hedging — use updated regime names
    diversified = diversify_signals(summary[summary['Regime'] == 'Trend Breakout'])
    exits = get_exit_recommendations(summary)
    
    # --- WAR-TIME TIME EXITS (Audit Sync) ---
    for pair, info in tracked_trades.items():
        if pair not in ["CL=F", "GC=F"]:
            continue
        entry_time = datetime.fromisoformat(info['entry_time'])
        limit_hours = 8 if pair == "GC=F" else 4
        if datetime.now() - entry_time > timedelta(hours=limit_hours):
            print(f"!!! WAR-TIME TIME EXIT: {pair} has been open for > {limit_hours} hours. !!!")
            if pair not in exits:
                exits.append(pair)
            # Remove from new tracker to "forget" this trade
            if pair in new_tracker:
                del new_tracker[pair]

    save_tracker(new_tracker)
    
    hedges = find_correlation_hedges(summary[summary['Regime'] == 'Trend Breakout'])
    
    # Sort summary by Cluster and Regime for consistent visual presentation in both Terminal and CSV
    summary = summary.sort_values(by=['Cluster', 'Regime'])

    print("\n--- Raw Analysis (All Pairs) ---", flush=True)
    print(summary[['Cluster', 'Regime', 'Direction', 'State', 'Warnings']], flush=True)
    
    print("\n--- Trend Breakout Assets (High Volatility — Big Moves) ---")
    breakouts = summary[summary['Regime'] == 'Trend Breakout']
    if not breakouts.empty:
        for idx, row in breakouts.iterrows():
            print(f"  *** BREAKOUT *** Asset: {idx} | Direction: {row['Direction']} [Cluster {row['Cluster']}]")
    else:
        print("None detected.")

    print("\n--- Mean Reversion Assets (High Volatility — Scalps) ---")
    trends = summary[summary['Regime'] == 'Mean Reversion']
    if not trends.empty:
        for idx, row in trends.iterrows():
            print(f"  *** SCALP *** Asset: {idx} | Direction: {row['Direction']} [Cluster {row['Cluster']}]")
    else:
        print("None detected.")

    print("\n--- Exit/Monitoring Recommendations ---")
    if exits:
        print(f"RECOMMENDATION: Consider closing or tightening stops on: {', '.join(exits)}")
    else:
        print("None.")

    print("\n--- Diversified Picks (Max One Per Cluster) ---")
    if not diversified.empty:
        print(diversified[['Cluster', 'Direction']])
    else:
        print("No breakout signals for new entry..")
        
    print("\n--- Market Neutral Correlation Hedges ---")
    if hedges:
        for h in hedges:
            print(f"Hedge: {h['Pair_A']} ({h['Dir_A']}) vs {h['Pair_B']} ({h['Dir_B']})")
    else:
        print("No hedging opportunities found.")
    
    # Save results
    summary.to_csv('analysis_summary.csv')
    print("\nComplete scan saved to 'analysis_summary.csv'.")

if __name__ == "__main__":
    main()
