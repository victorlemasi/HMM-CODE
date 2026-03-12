import pandas as pd
from data_fetcher import fetch_data, get_returns_matrix, get_macro_data
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
            is_breakout, direction, regime, _ = detect_breakout(df, ticker=pair, macro_data=macro_data)
            regime_results[pair] = regime
            breakout_directions[pair] = direction
            # Diagnostic: show how far each pair is from transitioning regimes
            print(f"  {pair:<12} | Regime: {regime:<15} | Dir: {direction}")
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
