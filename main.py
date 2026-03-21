import pandas as pd
import time
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional
import logging

# Setup standard logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fix Windows console encoding for emoji/unicode in direction strings
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from data_fetcher import fetch_data, get_returns_matrix, get_macro_data, fetch_watchdog_data
from clustering import cluster_assets, plot_clusters
from hmm_analysis import detect_breakout, get_dynamic_exit_levels, get_trigger_price, calculate_z_score, calculate_atr
from config import (
    CURRENCY_PAIRS, INTERVAL, PERIOD, N_CLUSTERS, GPR_SPIKE_THRESHOLD, 
    SAFE_HAVEN_TICKER, MAJORS_FIX_LIST, MAJORS_MACRO_ENABLE, 
    ASSET_MAPPINGS, YIELD_TICKERS, FRED_TICKERS, YIELD_THRESHOLD, CONFIRMATION_BUFFER, MAJORS_TP_MULTIPLIER,
    WATCHDOG_TICKERS
)
from gpr_fetcher import fetch_latest_gpr
# Macro & Sentiment fetchers are imported dynamically to save memory
from rebalancer import find_correlation_hedges, get_exit_recommendations
from macro_bouncer import (
    check_fundamental_gatekeeper, get_macro_weight
)

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
        self.paused_until: Optional[datetime] = None
        
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
                logger.warning(f"!!! JUMP DETECTED on {ticker} ({metric_name}: {score:.2f} | Limit: {threshold}) !!!")
                logger.warning("ACTION: Pausing all trading operations for 15 minutes.")
                self.paused_until = datetime.now() + timedelta(minutes=15)
                return True
        return False

def main():
    watchdog = JumpWatchdog(WATCHDOG_TICKERS)
    loop_count = 0
    
    while True:
        loop_count += 1
        tracked_trades = load_tracker()
        new_tracker = {} # Refresh to only keep active trades
        
        # 0. Global Sentiment Assessment
        logger.info(f"--- Market Sentiment & Risk Assessment [Loop {loop_count}] ---")
        gpr_val, is_gpr_spike, gpr_msg = fetch_latest_gpr(threshold_std=GPR_SPIKE_THRESHOLD)
        logger.info(gpr_msg)
        # 1. Fetch data
        logger.info("Currency Pair Analysis Pipeline")
        
        # --- INTRADAY RE-FITTING (4-Hour Window) ---
        if loop_count % 4 == 0:
            logger.info("      [HMM ADAPTATION] Triggering 4-hour Baum-Welch re-fitting for all assets...")
            from train_hmm import train_all_models
            train_all_models()
            logger.info("      [HMM ADAPTATION] Re-fitting complete. All models synced to current volatility.")

        # --- JUMP WATCHDOG CHECK ---
        if watchdog.check_for_jumps():
            logger.info("INFORMATIONAL: Trading paused due to market shock. Continuing analysis for observation.")

        data = fetch_data(CURRENCY_PAIRS, INTERVAL, PERIOD)
        
        if not data:
            logger.error("No data fetched. Retrying in 60s...")
            time.sleep(60)
            continue
            
        logger.info("Fetching Macro Context (Yields/Commodities/Rates)")
        macro_data = get_macro_data(INTERVAL, PERIOD)
        
        # 2. Clustering Analysis (Optimized via Silhouette)
        logger.info("Running Clustering Analysis")
        returns_df = pd.DataFrame({p: df['Returns'] for p, df in data.items()}).dropna()
        cluster_mapping, correlation_matrix = cluster_assets(returns_df)
        plot_clusters(correlation_matrix, cluster_mapping)
        logger.info("Clustering complete. Result saved to 'correlation_clusters.png'.")
        
        # 3. HMM Breakout Analysis (Enhanced with BIC and RSI)
        logger.info("Running HMM Regime Detection")
        regime_results = {}
        breakout_directions = {}
        warnings_dict = {}
        macro_statuses = {}
        macro_weights = {}
        
        for pair, df in data.items():
            try:
                pair_warnings = []
                if is_gpr_spike and pair == SAFE_HAVEN_TICKER:
                    pair_warnings.append("GPR Spike -> Safe Haven Priority")
                    
                regime, prob, direction, is_breakout, state_id, current_atr, kelly = detect_breakout(df, pair, macro_data)
                current_price = df['Close'].iloc[-1]
                
                # War-Time Oil Protection
                is_scalp = False
                if pair == "CL=F":
                    dxy_key = 'DX-Y.NYB'
                    if dxy_key in macro_data:
                        dxy_val = macro_data[dxy_key]['Close'].iloc[-1]
                        if dxy_val > 102.5:
                            is_scalp = True
                            pair_warnings.append("High DXY -> SCALP ONLY (Oil)")
                
                tp, sl = get_dynamic_exit_levels(regime, current_price, current_atr, direction, ticker=pair, is_scalp=is_scalp)
                
                if is_scalp:
                    logger.info(f"  {pair} | SCALP MODE: Applied 1:1 ATR targets.")
                
                # --- HYBRID MACRO GATEKEEPER (2026 Sync) ---
                gatekeeper_status = check_fundamental_gatekeeper(pair, df.index[-1], macro_data)
                macro_statuses[pair] = gatekeeper_status

                # Calculate 1.2 Candle Trigger for All Macro Pairs
                trigger = None
                if pair in ASSET_MAPPINGS and ASSET_MAPPINGS[pair]['type'] == 'macro':
                    macro_phase = "WIN_PHASE" if ("Bullish Bias" in gatekeeper_status or "Bearish Bias" in gatekeeper_status) else "TRAP_PHASE"
                    trigger = get_trigger_price(df, regime, direction, current_atr, macro_phase=macro_phase)
                
                macro_weight = get_macro_weight(pair, direction, macro_data)
                macro_weights[pair] = f"{macro_weight:.2f}x" # Save the Gravity Curve multiplier for the CSV
                adjusted_prob = prob * macro_weight
                
                # --- PHASE 4: REAL-TIME NLP SENTIMENT (SerpApi + FinBERT) ---
                if direction in ["LONG", "SHORT"] and regime in ["Trend Breakout", "Mean Reversion"]:
                    from sentiment_fetcher import get_realtime_sentiment_modifier
                    nlp_mult = get_realtime_sentiment_modifier(pair)
                    if nlp_mult != 1.0:
                        logger.info(f"  {pair} | NLP Sentiment Mod: {nlp_mult:.2f}x")
                        adjusted_prob *= nlp_mult
                        pair_warnings.append(f"NLP Sentiment: {nlp_mult:.2f}x")
                        
                # --- PHASE 5: HYBRID AI ENSEMBLING (XGBoost) ---
                # Pass the core HMM outputs through the massive XGBoost decision tree
                if regime in ["Trend Breakout", "Mean Reversion"] and direction in ["LONG", "SHORT"]:
                    import os, joblib
                    xgb_path = "xgb_breakout_filter.pkl"
                    if os.path.exists(xgb_path):
                        try:
                            xgb_model = joblib.load(xgb_path)
                            atr_norm = current_atr / current_price
                            # Features must exactly match generate_xgboost_dataset.py
                            X_live = pd.DataFrame([{
                                'state_id': state_id,
                                'hmm_confidence': prob,
                                'atr_normalized': atr_norm
                            }])
                            xgb_pred = xgb_model.predict(X_live)[0]
                            
                            if xgb_pred == 0:
                                logger.info(f"  [XGBOOST VETO] {pair} Signal Blocked. AI Ensemble classifies this as a liquidity trap.")
                                regime = "Consolidation"
                                direction = "None"
                                pair_warnings.append("XGBoost AI Veto")
                            else:
                                pair_warnings.append("XGBoost AI Confirmed")
                        except Exception as e:
                            logger.error(f"  [XGBOOST ERROR] Failed to run ensemble filter: {e}")
                
                # --- LUNCH ZONE FILTER (London Lunch / NY Pre-Open) ---
                hour_utc = datetime.now().hour
                LUNCH_ZONE_HOURS = (11, 13)
                conf_thresh = 0.85
                
                if pair in MAJORS_FIX_LIST and LUNCH_ZONE_HOURS[0] <= hour_utc < LUNCH_ZONE_HOURS[1]:
                    conf_thresh = 0.90
                    pair_warnings.append("LUNCH ZONE Penalty")
                    logger.info(f"  {pair} | LUNCH ZONE: Increasing confidence threshold to 0.90")

                if adjusted_prob < conf_thresh and direction not in ["None", "⚠️LONG", "⚠️SHORT"]:
                     logger.info(f"  [VETO] {pair} Signal Rejected: Low Contextual Confidence ({adjusted_prob:.2f} < {conf_thresh})")
                     pair_warnings.append(f"Low Confidence ({adjusted_prob:.2f} < {conf_thresh})")
                     direction = f"⚠️{direction}"

                # --- TRADE TRACKER & SYNC ---
                if pair in tracked_trades:
                    new_tracker[pair] = tracked_trades[pair]
                    new_tracker[pair]['bars_active'] = new_tracker[pair].get('bars_active', 0) + 1
                    
                    # --- SIGNAL EXPIRY (Differentiated: 3 bars FX / 2 bars Commodities) ---
                    expiry_limit = 3 if pair.endswith("=X") else 2
                    if new_tracker[pair]['bars_active'] >= expiry_limit:
                        logger.info(f"  [SIGNAL EXPIRED] {pair} failed to trigger within {expiry_limit} bars.")
                        direction = "None"
                        regime = "Consolidation" # Reset regime on expiry for consistency
                        del new_tracker[pair]
                    else:
                        # --- ATR CHANDELIER EXIT (Phase 3) ---
                        if new_tracker[pair].get('regime', 'Trend Breakout') == "Trend Breakout":
                            trail_dist = current_atr * 1.5
                            if new_tracker[pair]['direction'] == "LONG":
                                new_sl = current_price - trail_dist
                                if new_sl > new_tracker[pair].get('sl', 0):
                                    new_tracker[pair]['sl'] = new_sl
                                    logger.info(f"  {pair} | CHANDELIER EXIT: Trailed SL up to {new_sl:.5f}")
                            else:
                                new_sl = current_price + trail_dist
                                if new_sl < new_tracker[pair].get('sl', 999999):
                                    new_tracker[pair]['sl'] = new_sl
                                    logger.info(f"  {pair} | CHANDELIER EXIT: Trailed SL down to {new_sl:.5f}")
                        else:
                            # Standard Mean Reversion Protective Trail
                            pnl_atr = (current_price - new_tracker[pair]['entry_price']) / current_atr if new_tracker[pair]['direction'] == "LONG" else (new_tracker[pair]['entry_price'] - current_price) / current_atr
                            if pnl_atr > 0.8:
                                new_sl = current_price - current_atr if new_tracker[pair]['direction'] == "LONG" else current_price + current_atr
                                if new_tracker[pair]['direction'] == "LONG":
                                    new_tracker[pair]['sl'] = max(new_tracker[pair].get('sl', 0), new_sl)
                                else:
                                    new_tracker[pair]['sl'] = min(new_tracker[pair].get('sl', 999999), new_sl)
                                logger.info(f"  {pair} | PROGRESSIVE STOP: Tightened SL to {new_tracker[pair]['sl']:.5f}")
                else:
                    # New Entry
                    if direction in ["LONG", "SHORT"]:
                        new_tracker[pair] = {
                            'entry_price': current_price,
                            'entry_time': datetime.now().isoformat(),
                            'tp': tp,
                            'sl': sl,
                            'direction': direction,
                            'bars_active': 0,
                            'regime': regime,
                            'kelly_size': round(kelly, 2)
                        }

                msg = f"  {pair} | Regime: {regime:15} | Bias: {direction:7} | Conf: {adjusted_prob:.2f}"
                if tp:
                    msg += f" | TP: {tp:.5f} | SL: {sl:.5f}"
                if trigger:
                    msg += f" | TRIGGER: {trigger:.5f}"
                logger.info(msg)

                # --- FINAL STATE UPDATE (Ensure CSV matches Terminal) ---
                regime_results[pair] = regime
                breakout_directions[pair] = direction
                warnings_dict[pair] = " | ".join(pair_warnings) if pair_warnings else ""

            except Exception as e:
                logger.error(f"Error analyzing {pair}: {e}")
                regime_results[pair] = "Error"
                breakout_directions[pair] = "None"
        
        summary = pd.DataFrame.from_dict(regime_results, orient='index', columns=['Regime'])
        summary['Direction'] = pd.Series(breakout_directions)
        summary['Cluster'] = pd.Series(cluster_mapping)
        summary['State'] = pd.Series(macro_statuses)
        summary['Macro_Weight'] = pd.Series(macro_weights)
        summary['Warnings'] = pd.Series(warnings_dict)
        
        logger.info("Risk Overlay")
        if is_gpr_spike:
            logger.warning("!!! WARNING: GEOPOLITICAL RISK SPIKING !!!")
            logger.warning("ACTION: Switching to SAFE HAVEN mode.")
            logger.warning(f"FOCUS: Prioritize {SAFE_HAVEN_TICKER} (Gold) signals.")
        
        # Diversification & Portfolio Optimization
        active_positions = list(new_tracker.keys())
        from rebalancer import optimize_portfolio_weights, get_exit_recommendations, find_correlation_hedges
        optimal_weights = optimize_portfolio_weights(active_positions, returns_df)
        
        exits = get_exit_recommendations(summary)
        
        # --- WAR-TIME TIME EXITS (Audit Sync) ---
        for pair, info in tracked_trades.items():
            if pair not in ["CL=F", "GC=F"]:
                continue
            entry_time_dt = datetime.fromisoformat(info['entry_time'])
            limit_hours = 8 if pair == "GC=F" else 4
            if datetime.now() - entry_time_dt > timedelta(hours=limit_hours):
                logger.warning(f"!!! WAR-TIME TIME EXIT: {pair} has been open for > {limit_hours} hours. !!!")
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
        
        logger.info("Trend Breakout Assets (High Volatility — Big Moves)")
        breakouts = summary[summary['Regime'] == 'Trend Breakout']
        if not breakouts.empty:
            for idx, row in breakouts.iterrows():
                logger.info(f"  *** BREAKOUT *** Asset: {idx} | Direction: {row['Direction']} [Cluster {row['Cluster']}]")
        else:
            logger.info("None detected.")

        logger.info("Mean Reversion Assets (High Volatility — Scalps)")
        trends = summary[summary['Regime'] == 'Mean Reversion']
        if not trends.empty:
            for idx, row in trends.iterrows():
                logger.info(f"  *** SCALP *** Asset: {idx} | Direction: {row['Direction']} [Cluster {row['Cluster']}]")
        else:
            logger.info("None detected.")

        logger.info("Exit/Monitoring Recommendations")
        if exits:
            logger.info(f"RECOMMENDATION: Consider closing or tightening stops on: {', '.join(exits)}")
        else:
            logger.info("None.")

        logger.info("Markowitz Optimal Portfolio Weights (Active Positions)")
        if optimal_weights:
            for ast, weight in optimal_weights.items():
                logger.info(f"  {ast}: {weight*100:.1f}%")
        else:
            logger.info("No active positions to optimize.")
            
        logger.info("Market Neutral Correlation Hedges")
        if hedges:
            for h in hedges:
                logger.info(f"Hedge: {h['Pair_A']} ({h['Dir_A']}) vs {h['Pair_B']} ({h['Dir_B']})")
        else:
            logger.info("No hedging opportunities found.")
        
        # Save results
        summary.to_csv('analysis_summary.csv')
        logger.info("Complete scan saved to 'analysis_summary.csv'.")
        
        logger.info(f"Loop {loop_count} complete. Waiting 5 minutes...")
        time.sleep(300)

if __name__ == "__main__":
    main()
