import pandas as pd
from data_fetcher import fetch_data
from clustering import cluster_assets
from hmm_analysis import detect_breakout
from config import CURRENCY_PAIRS, INTERVAL, PERIOD, GPR_SPIKE_THRESHOLD
from gpr_fetcher import fetch_historical_gpr
from backtester import run_backtest
import os

def run_standalone():
    print("=== Standalone Backtest Execution ===")
    
    # 1. Fetch historical data
    print(f"Fetching {PERIOD} of {INTERVAL} data for {len(CURRENCY_PAIRS)} assets...")
    data = fetch_data(CURRENCY_PAIRS, INTERVAL, PERIOD)
    
    if not data:
        print("No data fetched. Exiting.")
        return

    # 2. Prepare Returns Matrix
    returns_df = pd.DataFrame({p: df['Returns'] for p, df in data.items()}).dropna()
    print(f"Returns Matrix built: {returns_df.shape}")
    
    # 3. Clustering
    cluster_mapping, _ = cluster_assets(returns_df)
    
    # 4. HMM Historical State Generation
    print("Generating HMM life-cycle states for all assets...")
    hist_states_dict = {}
    breakout_map = {}
    
    for pair, df in data.items():
        try:
            # We use the full history to fit the HMM and get states
            _, _, hist_states, breakout_state = detect_breakout(df)
            hist_states_dict[pair] = hist_states
            breakout_map[pair] = breakout_state
        except Exception as e:
            print(f"Error analyzing {pair}: {e}")
            continue
            
    hist_states_df = pd.DataFrame(hist_states_dict).dropna()
    
    # Align returns with states
    aligned_returns = returns_df.loc[hist_states_df.index]
    
    # 5. Fetch Historical GPR
    hist_gpr = fetch_historical_gpr(threshold_std=GPR_SPIKE_THRESHOLD)
    
    if hist_states_df.empty:
        print("Error: Historical states could not be aligned.")
        return

    # 6. Run Backtest
    print("\n--- Starting Simulation ---")
    results = run_backtest(
        aligned_returns,
        hist_states_df,
        breakout_map,
        cluster_mapping,
        hist_gpr
    )
    
    print("\n=== FINAL BACKTEST RESULTS (Last 60 Days) ===")
    for k, v in results.items():
        if k != "Equity Curve":
            print(f"{k}: {v}")
            
    # Save results to a specialized CSV
    results_df = pd.DataFrame({
        "Metrics": [k for k in results.keys() if k != "Equity Curve"],
        "Values": [results[k] for k in results.keys() if k != "Equity Curve"]
    })
    results_df.to_csv("backtest_results.csv", index=False)
    print("\nResults saved to 'backtest_results.csv'.")

if __name__ == "__main__":
    run_standalone()
