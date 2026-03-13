import pandas as pd
from data_fetcher import fetch_data, get_returns_matrix, get_macro_data
from clustering import cluster_assets, plot_clusters
from hmm_analysis import detect_breakout, get_dynamic_exit_levels, get_trigger_price
from config import (
    CURRENCY_PAIRS, INTERVAL, PERIOD, N_CLUSTERS, GPR_SPIKE_THRESHOLD, 
    SAFE_HAVEN_TICKER, MAJORS_FIX_LIST, MAJORS_MACRO_ENABLE, 
    ASSET_MAPPINGS, YIELD_TICKERS, YIELD_THRESHOLD, CONFIRMATION_BUFFER, MAJORS_TP_MULTIPLIER
)
from gpr_fetcher import fetch_latest_gpr

from sentiment_fetcher import fetch_market_sentiment
from rebalancer import diversify_signals, find_correlation_hedges, get_exit_recommendations

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

def get_macro_permission(pair):
    """
    Acts as a 'Bouncer' for EURUSD trades based on institutional fundamentals.
    """
    if pair != "EURUSD=X":
        return "ALLOW" # Don't interfere with your winning Gold/CHF pairs

    try:
        import yfinance as yf
        # 1. Fetch Proxy Fundamental Data
        dxy = yf.Ticker("DX-Y.NYB").history(period="2d")['Close']
        oil = yf.Ticker("CL=F").history(period="2d")['Close']
        
        if len(dxy) < 2 or len(oil) < 1:
            return "ALLOW"
            
        dxy_change = (dxy.iloc[-1] - dxy.iloc[-2]) / dxy.iloc[-2]
        current_oil = oil.iloc[-1]

        # 2. Institutional Logic (March 2026 Context)
        # If USD is getting stronger (DXY up) or Energy is expensive (Oil up)
        # the Euro is fundamentally weak.
        if dxy_change > 0.002 or current_oil > 95:
            return "SHORT_ONLY"
        
        elif dxy_change < -0.002 and current_oil < 80:
            return "LONG_ONLY"
            
        return "ALLOW"
        
    except Exception as e:
        print(f"Macro Filter Error: {e}")
        return "ALLOW" # Fallback to standard logic if data fails

def main():
    # 0. Global Sentiment Assessment
    print("\n--- Market Sentiment & Risk Assessment ---")
    gpr_val, is_gpr_spike, gpr_msg = fetch_latest_gpr(threshold_std=GPR_SPIKE_THRESHOLD)
    print(gpr_msg)
    
    sent_val, sent_class, sent_recom = fetch_market_sentiment()
    print(f"Market Sentiment: {sent_val} ({sent_class}) -> RECOMMENDATION: {sent_recom}")
    
    # 1. Fetch data
    print("\n=== Currency Pair Analysis Pipeline ===")
    data = fetch_data(CURRENCY_PAIRS, INTERVAL, PERIOD)
    
    if not data:
        print("No data fetched. Exiting.")
        return
        
    print("\n--- Fetching Macro Context (Yields/Commodities) ---")
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
            is_breakout, direction, regime, _, current_atr = detect_breakout(df, ticker=pair, macro_data=macro_data)
            regime_results[pair] = regime
            
            # Calculate Dynamic Exit Levels
            current_price = df['Close'].iloc[-1]
            tp, sl = get_dynamic_exit_levels(regime, current_price, current_atr, direction, ticker=pair)
            
            # Calculate 1.2 Candle Trigger for Majors
            trigger = None
            macro_phase = "TRAP_PHASE"
            if pair in MAJORS_FIX_LIST and regime == "Trend Breakout":
                macro_phase = check_macro_alignment(pair, direction, macro_data)
            
            # --- APPLY THE FUNDAMENTAL BOUNCER ---
            macro_bias = get_macro_permission(pair)
            if macro_bias == "SHORT_ONLY" and direction == "LONG":
                print(f"  {pair} | SIGNAL REJECTED: Macro bias is Bearish.")
                direction = "None"
            elif macro_bias == "LONG_ONLY" and direction == "SHORT":
                print(f"  {pair} | SIGNAL REJECTED: Macro bias is Bullish.")
                direction = "None"
            
            # Calculate 1.2 Candle Trigger for Majors
            trigger = None
            if pair in MAJORS_FIX_LIST and regime == "Trend Breakout" and direction != "None":
                trigger = get_trigger_price(df, regime, direction, current_atr, macro_phase=macro_phase)
                # print(f" {pair} | Running OPTIMIZED Major Logic...") # Removed to keep standard formatting clean
            elif regime == "Trend Breakout" and direction != "None":
                trigger = get_trigger_price(df, regime, direction, current_atr, macro_phase="WIN_PHASE")
                # print(f" {pair} | Running STANDARD Logic (Win-streak active)") # Removed to keep standard formatting clean
            
            # Update summary direction AFTER all filters
            breakout_directions[pair] = direction
            
            # Diagnostic: show current state
            msg = f"  {pair:<12} | Regime: {regime:<15} | Dir: {direction}"
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
