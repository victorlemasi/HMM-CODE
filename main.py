import pandas as pd
from data_fetcher import fetch_data, get_returns_matrix
from clustering import cluster_assets, plot_clusters
from hmm_analysis import detect_breakout
from config import CURRENCY_PAIRS

def main():
    print("=== Currency Pair Analysis Pipeline ===")
    
    # 1. Fetch Data
    data = fetch_data()
    if not data:
        print("Error: No data fetched.")
        return
    
    # 2. Clustering Analysis
    print("\n--- Running Clustering Analysis ---")
    returns_df = get_returns_matrix(data)
    cluster_mapping, correlation_matrix = cluster_assets(returns_df)
    plot_clusters(correlation_matrix, cluster_mapping)
    print("Clustering complete. Saved 'correlation_clusters.png'.")
    
    # 3. HMM Breakout Analysis
    print("\n--- Running HMM Breakout Detection ---")
    breakout_states = {}
    breakout_directions = {}
    for pair, df in data.items():
        try:
            is_breakout, direction, states, breakout_state = detect_breakout(df)
            breakout_states[pair] = "BREAKOUT" if is_breakout else "Normal"
            breakout_directions[pair] = direction if is_breakout else "None"
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
    
    # Diversification Check
    from rebalancer import diversify_signals, find_correlation_hedges
    diversified = diversify_signals(summary)
    hedges = find_correlation_hedges(summary)
    
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
    
    # Save results
    summary.to_csv('analysis_summary.csv')
    print("\nComplete scan saved to 'analysis_summary.csv'.")

if __name__ == "__main__":
    main()
