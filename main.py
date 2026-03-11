import pandas as pd
from data_fetcher import fetch_data, get_returns_matrix
from clustering import cluster_assets, plot_clusters
from hmm_analysis import detect_breakout
from config import CURRENCY_PAIRS, INTERVAL, PERIOD, N_CLUSTERS, GPR_SPIKE_THRESHOLD, SAFE_HAVEN_TICKER
from gpr_fetcher import fetch_latest_gpr

from sentiment_fetcher import fetch_market_sentiment
from rebalancer import diversify_signals, find_correlation_hedges, get_exit_recommendations

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
            is_breakout, direction, regime, _ = detect_breakout(df)
            regime_results[pair] = regime
            breakout_directions[pair] = direction
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

    # Diversification & Hedging
    diversified = diversify_signals(summary[summary['Regime'] == 'Breakout'])
    exits = get_exit_recommendations(summary)
    hedges = find_correlation_hedges(summary[summary['Regime'] == 'Breakout'])
    
    print("\n--- Raw Analysis ---")
    print(summary[['Cluster', 'Regime', 'Direction']].sort_values(by=['Cluster', 'Regime']))
    
    print("\n--- Diversified Breakout Picks ---")
    if not diversified.empty:
        print(diversified[['Cluster', 'Direction']])
    else:
        print("No breakout signals detected.")
        
    print("\n--- Exit/Profit-Taking Recommendations ---")
    # Show assets that were previously trending/breaking but are now in Consolidation or Stable
    print(f"Assets marked for Exit/Monitoring: {', '.join(exits[:5])}...")
        
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
