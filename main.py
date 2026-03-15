import pandas as pd
import time
from datetime import datetime, timedelta
from data_fetcher import fetch_data, get_returns_matrix, get_macro_data, fetch_watchdog_data
from clustering import cluster_assets, plot_clusters
from hmm_analysis import detect_breakout, get_dynamic_exit_levels, get_trigger_price, calculate_z_score
from config import (
    CURRENCY_PAIRS, INTERVAL, PERIOD, N_CLUSTERS, GPR_SPIKE_THRESHOLD, 
    SAFE_HAVEN_TICKER, MAJORS_FIX_LIST, MAJORS_MACRO_ENABLE, 
    ASSET_MAPPINGS, YIELD_TICKERS, YIELD_THRESHOLD, CONFIRMATION_BUFFER, MAJORS_TP_MULTIPLIER,
    WATCHDOG_TICKERS
)
from gpr_fetcher import fetch_latest_gpr

from sentiment_fetcher import fetch_market_sentiment
from rebalancer import diversify_signals, find_correlation_hedges, get_exit_recommendations
from macro_bouncer import check_fundamental_gatekeeper, get_macro_weight

class TradeTracker:
    def __init__(self, filename="trade_tracker.json"):
        self.filename = filename
        self.active_signals = self._load()
        
    def _load(self):
        import os, json
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                try: 
                    data = json.load(f)
                    # Convert strings back to datetimes
                    return {k: datetime.fromisoformat(v) for k, v in data.items()}
                except: return {}
        return {}
        
    def _save(self):
        import json
        with open(self.filename, 'w') as f:
            data = {k: v.isoformat() for k, v in self.active_signals.items()}
            json.dump(data, f)
            
    def update_signal(self, ticker, direction):
        if direction == "None":
            if ticker in self.active_signals:
                del self.active_signals[ticker]
                self._save()
            return False
            
        if ticker not in self.active_signals:
            self.active_signals[ticker] = datetime.now()
            self._save()
            return False
            
        # Check duration
        duration = datetime.now() - self.active_signals[ticker]
        if ticker in ["CL=F"] and duration.total_seconds() > 4 * 3600:
            return True # EXIT SIGNAL
        return False

class JumpWatchdog:
    def __init__(self, tickers):
        self.tickers = tickers
        self.lock_file = "watchdog_pause.lock"
        self.paused_until = self._load_pause()
        
    def _load_pause(self):
        import os
        if os.path.exists(self.lock_file):
            with open(self.lock_file, 'r') as f:
                try:
                    ts = float(f.read().strip())
                    dt = datetime.fromtimestamp(ts)
                    if dt > datetime.now():
                        return dt
                except:
                    pass
        return None

    def _save_pause(self, dt):
        with open(self.lock_file, 'w') as f:
            f.write(str(dt.timestamp()))

    def check_for_jumps(self):
        if self.paused_until and datetime.now() < self.paused_until:
            return True
            
        from config import WATCHDOG_JUMP_THRESHOLDS
        print("\n--- Running 1-Minute Jump Watchdog ---")
        wd_data = fetch_watchdog_data(self.tickers)
        for ticker, df in wd_data.items():
            z_score = calculate_z_score(df['Close'])
            # Use specific threshold or fallback to DEFAULT
            threshold = WATCHDOG_JUMP_THRESHOLDS.get(ticker, WATCHDOG_JUMP_THRESHOLDS['DEFAULT'])
            
            if abs(z_score) > threshold:
                print(f"!!! JUMP DETECTED on {ticker} (Z-Score: {z_score:.2f} | Limit: {threshold}) !!!")
                print("ACTION: Pausing all trading operations for 15 minutes.")
                pause_dt = datetime.now() + timedelta(minutes=15)
                self.paused_until = pause_dt
                self._save_pause(pause_dt)
                return True
        return False

    def get_remaining_pause_minutes(self):
        if not self.paused_until:
            return 0
        diff = self.paused_until - datetime.now()
        return max(0, int(diff.total_seconds() / 60))

def get_yield_spread_momentum(ticker, macro_data):
    """
    Calculates the 5-bar trend of the yield spread.
    Positive means Base Yield is rising faster than Quote Yield.
    """
    if ticker not in ASSET_MAPPINGS or ASSET_MAPPINGS[ticker]['type'] != 'macro':
        return 0
        
    mapping = ASSET_MAPPINGS[ticker]
    base_ticker = YIELD_TICKERS.get(mapping['base'])
    quote_ticker = YIELD_TICKERS.get(mapping['quote'])
    
    if base_ticker not in macro_data or quote_ticker not in macro_data or macro_data[base_ticker].empty or macro_data[quote_ticker].empty:
        # Fallback to DXY momentum
        dxy_ticker = YIELD_TICKERS.get('DXY')
        if dxy_ticker in macro_data and not macro_data[dxy_ticker].empty:
            dxy_df = macro_data[dxy_ticker]
            if len(dxy_df) >= 6:
                # If DXY is rising, USD is strengthening -> Negative momentum for EURUSD/GBPUSD
                momentum = dxy_df['Close'].iloc[-1] - dxy_df['Close'].iloc[-5]
                return -momentum
        return 0
        
    base_df = macro_data[base_ticker]
    quote_df = macro_data[quote_ticker]
    
    # Calculate spread
    spread = base_df['Close'] - quote_df['Close']
    
    # 5-bar momentum
    if len(spread) < 6:
        return 0
        
    momentum = spread.iloc[-1] - spread.iloc[-5]
    return momentum

def check_macro_alignment(ticker, direction, macro_data):
    """
    Determines if the macro trend supports the technical breakout.
    """
    if not MAJORS_MACRO_ENABLE or ticker not in MAJORS_FIX_LIST:
        return "TRAP_PHASE"
        
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
    tracker = TradeTracker()
    
    # 0. Global Sentiment Assessment
    print("\n--- Market Sentiment & Risk Assessment ---")
    gpr_val, is_gpr_spike, gpr_msg = fetch_latest_gpr(threshold_std=GPR_SPIKE_THRESHOLD)
    print(gpr_msg)
    
    sent_val, sent_class, sent_recom = fetch_market_sentiment()
    print(f"Market Sentiment: {sent_val} ({sent_class}) -> RECOMMENDATION: {sent_recom}")
    
    # 1. Fetch data
    print("\n=== Currency Pair Analysis Pipeline ===")
    
    # --- JUMP WATCHDOG CHECK ---
    is_shock_paused = watchdog.check_for_jumps()
    if is_shock_paused:
        rem = watchdog.get_remaining_pause_minutes()
        print(f"!!! WARNING: Trading paused (Market Shock). Resuming in {rem} minutes. !!!")
        print("!!! Analysis shown for INFORMATION ONLY. Automated trading BLOCKED. !!!")

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
    
    for pair, df in data.items():
        try:
            is_breakout, direction, regime, _, current_atr, prob = detect_breakout(df, ticker=pair, macro_data=macro_data)
            regime_results[pair] = regime
            raw_direction = direction
            veto_flag = False
            veto_reason = None
            
            # --- APPLY MACRO WEIGHTING ---
            macro_weight = get_macro_weight(pair, direction, macro_data)
            adjusted_prob = prob * macro_weight
            
            # Calculate Dynamic Exit Levels
            current_price = df['Close'].iloc[-1]
            tp, sl = get_dynamic_exit_levels(regime, current_price, current_atr, direction, ticker=pair)
            
            # Calculate 1.2 Candle Trigger for Majors
            trigger = None
            macro_phase = "TRAP_PHASE"
            if pair in MAJORS_FIX_LIST and regime == "Trend Breakout":
                macro_phase = check_macro_alignment(pair, direction, macro_data)
            
            # --- APPLY THE FUNDAMENTAL BOUNCER (Global Gatekeeper) ---
            current_time = df.index[-1]
            gatekeeper_status = check_fundamental_gatekeeper(pair, current_time, macro_data)
            
            if gatekeeper_status == "BEARISH_ONLY" and direction == "LONG":
                print(f"  [VETO] {pair} LONG signal rejected: Macro Bias.")
                direction = "None"
                veto_flag = True
                veto_reason = "Macro Bias"
            elif gatekeeper_status == "BULLISH_ONLY" and direction == "SHORT":
                print(f"  [VETO] {pair} SHORT signal rejected: Macro Bias.")
                direction = "None"
                veto_flag = True
                veto_reason = "Macro Bias"
            elif gatekeeper_status == "SCALP_ONLY" and pair == "CL=F":
                print(f"  {pair} | WAR-TIME SCALP MODE: Tightening TP/SL.")
                # Override TP/SL with 1:1 Risk/Reward
                risk = current_atr * 2
                tp = current_price + (1 if direction == "LONG" else -1) * risk
                sl = current_price - (1 if direction == "LONG" else -1) * risk
            
            # --- CONFIDENCE THRESHOLD ---
            if adjusted_prob < 0.6 and direction != "None":
                 print(f"  [VETO] {pair} Signal Rejected: Low Macro-Adjusted Confidence ({adjusted_prob:.2f})")
                 direction = "None"
                 veto_flag = True
                 veto_reason = "Low Confidence"

            # Calculate 1.2 Candle Trigger for Majors
            trigger = None
            if pair in MAJORS_FIX_LIST and regime == "Trend Breakout" and direction != "None":
                trigger = get_trigger_price(df, regime, direction, current_atr, macro_phase=macro_phase)
            elif regime == "Trend Breakout" and direction != "None":
                trigger = get_trigger_price(df, regime, direction, current_atr, macro_phase="WIN_PHASE")
            
            # --- FINAL SIGNAL TAGGING ---
            # Priority: EXIT > SHOCK PAUSE > WARNING > NORMAL
            should_exit = tracker.update_signal(pair, direction)
            if should_exit:
                breakout_directions[pair] = "EXIT"
                direction = "None"
            elif is_shock_paused and raw_direction != "None":
                breakout_directions[pair] = f"{raw_direction} (SHOCK PAUSE)"
                direction = "None"
            elif veto_flag and raw_direction != "None":
                tag = f" ({veto_reason})" if veto_reason else " (WARNING)"
                breakout_directions[pair] = f"{raw_direction}{tag}"
                direction = "None"
            else:
                breakout_directions[pair] = direction

            # Diagnostic: show current state
            msg = f"  {pair:<12} | Regime: {regime:<15} | Dir: {breakout_directions[pair]} | Conf: {adjusted_prob:.2f}"
            if pair in MAJORS_FIX_LIST and regime == "Trend Breakout":
                msg += f" | Macro: {macro_phase}"
            if tp and sl:
                msg += f" | TP: {tp:.5f} | SL: {sl:.5f}"
            if trigger:
                msg += f" | TRIGGER: {trigger:.5f}"
            print(msg)
        except Exception as e:
            print(f"Error analyzing {pair}: {e}")
            regime_results[pair] = "Error"
            breakout_directions[pair] = "None"
    
    # 4. Final Summary
    print("\n=== Summary Report ===")
    summary = pd.DataFrame(index=returns_df.columns)
    summary['Cluster'] = cluster_mapping
    summary['Regime'] = pd.Series(regime_results)
    summary['Direction'] = pd.Series(breakout_directions)
    summary['State'] = summary['Regime'] # For compatibility with rebalancer
    
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
    hedges = find_correlation_hedges(summary[summary['Regime'] == 'Trend Breakout'])
    
    print("\n--- Raw Analysis (All Pairs) ---", flush=True)
    print(summary[['Cluster', 'Regime', 'Direction', 'State']].sort_values(by=['Cluster', 'Regime']), flush=True)
    
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
