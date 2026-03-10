import pandas as pd
from data_fetcher import fetch_data, get_returns_matrix
from clustering import cluster_assets, plot_clusters
from hmm_analysis import detect_breakout
from config import CURRENCY_PAIRS, INTERVAL, PERIOD, N_CLUSTERS, GPR_SPIKE_THRESHOLD, SAFE_HAVEN_TICKER
from gpr_fetcher import fetch_latest_gpr

def main():
    # 0. GPR Risk Assessment
    print("\n--- Geopolitical Risk (GPR) Assessment ---")
    
    gpr_val, is_gpr_spike, gpr_msg = fetch_latest_gpr(threshold_std=GPR_SPIKE_THRESHOLD)
    print(gpr_msg)
    
    # 1. Fetch data
    print("\n=== Currency Pair Analysis Pipeline ===")
    data = fetch_data(CURRENCY_PAIRS, INTERVAL, PERIOD)
    
    if not data:
        print("No data fetched. Exiting.")
        return
    
    # 2. Clustering Analysis
    print("\n--- Running Clustering Analysis ---")
    returns_df = pd.DataFrame({p: df['Returns'] for p, df in data.items()}).dropna()
    print(f"Returns Matrix built: {returns_df.shape}")
    
    cluster_mapping, correlation_matrix = cluster_assets(returns_df)
    plot_clusters(correlation_matrix, cluster_mapping)
    print("Clustering complete. Saved 'correlation_clusters.png'.")
    
    # 3. HMM Breakout Analysis
    print("\n--- Running HMM Breakout Detection ---")
    breakout_states = {}
    breakout_directions = {}
    hist_states_dict = {}
    breakout_map = {}
    
    for pair, df in data.items():
        try:
            is_breakout, direction, hist_states, breakout_state = detect_breakout(df)
            breakout_states[pair] = "BREAKOUT" if is_breakout else "Normal"
            breakout_directions[pair] = direction if is_breakout else "None"
            
            hist_states_dict[pair] = hist_states
            breakout_map[pair] = breakout_state
        except Exception as e:
            print(f"Error analyzing {pair}: {e}")
            breakout_states[pair] = "Error"
            breakout_directions[pair] = "None"
    
    # 4. Final Summary
    print("\n=== Summary Report ===")
    summary = pd.DataFrame(index=returns_df.columns)
    summary['Cluster'] = cluster_mapping
    summary['State'] = pd.Series(breakout_states)
    summary['Direction'] = pd.Series(breakout_directions)
    
    # GPR Logic: Safe Haven Mode
    print("\n--- Risk Overlay ---")
    if is_gpr_spike:
        print("!!! WARNING: GEOPOLITICAL RISK SPIKING !!!")
        print("ACTION: Switching to SAFE HAVEN mode.")
        print("RECOM: Reduce ALL leverage by 50%.")
        print(f"FOCUS: Prioritize {SAFE_HAVEN_TICKER} (Gold) signals.")
    else:
        print("GPR Risk: Normal. Standard risk management applies.")
    
    # Diversification & Hedging
    from rebalancer import diversify_signals, find_correlation_hedges
    diversified = diversify_signals(summary)
    hedges = find_correlation_hedges(summary)
    
    # If GPR Spiking, focus diversified picks on Safe Haven if available
    if is_gpr_spike and SAFE_HAVEN_TICKER in summary.index:
        if summary.loc[SAFE_HAVEN_TICKER, 'State'] == 'BREAKOUT':
            print(f"\n[ALERT] Safe Haven {SAFE_HAVEN_TICKER} is in BREAKOUT!")
    
    print("\n--- Raw Analysis ---")
    print(summary.sort_values(by=['Cluster', 'State']))
    
    print("\n--- Diversified Picks (One per Cluster) ---")
    if not diversified.empty:
        print(diversified[['Cluster', 'Direction']])
    else:
        print("No breakout signals detected for diversification.")
        
    print("\n--- Market Neutral Correlation Hedges ---")
    if hedges:
        for h in hedges:
            print(f"Hedge: {h['Pair_A']} ({h['Dir_A']}) vs {h['Pair_B']} ({h['Dir_B']}) [Clusters {h['Cluster_A']} & {h['Cluster_B']}]")
    else:
        print("No hedging opportunities found.")

    # 5. Backtesting
    print("\n--- Running Historical Backtest (60-Day Lookback) ---")
    from backtester import run_backtest
    from gpr_fetcher import fetch_historical_gpr
    
    hist_states_df = pd.DataFrame(hist_states_dict).dropna()
    aligned_returns = returns_df.loc[hist_states_df.index]
    hist_gpr = fetch_historical_gpr(threshold_std=GPR_SPIKE_THRESHOLD)
    
    if not hist_states_df.empty:
        bt_metrics = run_backtest(
            aligned_returns, 
            hist_states_df, 
            breakout_map, 
            cluster_mapping, 
            hist_gpr
        )
        
        print("\n--- Backtest Results ---")
        for k, v in bt_metrics.items():
            if k != "Equity Curve":
                print(f"{k}: {v}")
    
    # Save results
    summary.to_csv('analysis_summary.csv')
    print("\nComplete scan saved to 'analysis_summary.csv'.")

if __name__ == "__main__":
    main()
