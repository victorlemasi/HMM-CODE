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
    breakout_results = {}
    for pair, df in data.items():
        try:
            is_breakout, states, breakout_state = detect_breakout(df)
            breakout_results[pair] = "BREAKOUT" if is_breakout else "Normal"
        except Exception as e:
            print(f"Error analyzing {pair}: {e}")
            breakout_results[pair] = "Error"
    
    # 4. Final Summary
    print("\n=== Summary Report ===")
    
    print(f"Cluster Mapping length: {len(cluster_mapping)}")
    print(f"Breakout Results length: {len(breakout_results)}")
    
    # Use index-based join to avoid issues
    summary = pd.DataFrame(index=returns_df.columns)
    summary['Cluster'] = cluster_mapping
    summary['State'] = pd.Series(breakout_results)
    
    # Handle missing values if any
    summary = summary.fillna("Data Error")
    
    # Format and display
    print(summary.sort_values(by=['Cluster', 'State']))
    
    # Save results
    summary.to_csv('analysis_summary.csv')
    print("\nComplete scan saved to 'analysis_summary.csv'.")

if __name__ == "__main__":
    main()
