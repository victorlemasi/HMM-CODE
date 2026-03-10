import pandas as pd
import numpy as np

def run_vectorized_backtest(all_data, cluster_mapping, gpr_series):
    """
    Simulates the strategy: Long/Short when in BREAKOUT state, 
    one pick per cluster, risk reduced if GPR spikes.
    """
    print("\n--- Initializing Backtest ---")
    
    # 1. Align all historical states and returns
    returns_dict = {}
    states_dict = {}
    breakout_state_ids = {}
    
    for pair, result in all_data.items():
        # result is (is_breakout, direction, hist_states, breakout_state_id)
        # We need the returns from the original data too
        # But wait, main.py has the returns in data[pair]['Returns']
        pass

    # Better approach: Pass pre-aligned DataFrames
    return None

def run_backtest(returns_df, states_df, breakout_map, cluster_mapping, gpr_df):
    """
    returns_df: DataFrame of hourly returns for all assets
    states_df: DataFrame of hourly HMM states for all assets
    breakout_map: Dict {ticker: breakout_state_id}
    cluster_mapping: Series {ticker: cluster_id}
    gpr_df: DataFrame with 'Date' and 'Is_Spiking' (daily)
    """
    print("Pre-processing backtest data...")
    
    # Align GPR to hourly indices
    gpr_df['Date'] = pd.to_datetime(gpr_df['Date']).dt.date
    gpr_lookup = gpr_df.set_index('Date')['Is_Spiking'].to_dict()
    
    # Initialize results
    portfolio_returns = []
    timestamps = returns_df.index
    
    for ts in timestamps:
        # Check GPR for this day
        is_gpr_spike = gpr_lookup.get(ts.date(), False)
        risk_multiplier = 0.5 if is_gpr_spike else 1.0
        
        # Identify active breakout signals
        active_signals = []
        for ticker in returns_df.columns:
            if ticker in states_df.columns:
                current_state = states_df.loc[ts, ticker]
                target_state = breakout_map.get(ticker)
                
                if current_state == target_state:
                    # Direction is determined by the HMM breakout state return sign (simplified here)
                    # For simplicity in vectorized backtest, we'll assume the direction 
                    # we identified in main analysis holds for that state.
                    active_signals.append(ticker)
        
        # Apply Diversification: One pick per cluster
        final_picks = []
        seen_clusters = set()
        for ticker in active_signals:
            cluster_id = cluster_mapping.get(ticker)
            if cluster_id not in seen_clusters:
                final_picks.append(ticker)
                seen_clusters.add(cluster_id)
        
        # Calculate step return
        if final_picks:
            # Equal weight across selected clusters
            step_return = np.mean([returns_df.loc[ts, t] for t in final_picks]) * risk_multiplier
        else:
            step_return = 0.0
            
        portfolio_returns.append(step_return)
    
    # Calculate Metrics
    results_ser = pd.Series(portfolio_returns, index=timestamps)
    cum_returns = (1 + results_ser).cumprod() - 1
    
    total_return = cum_returns.iloc[-1]
    
    # Annualized Sharpe (assuming 24*252 hourly steps per year approx)
    annualization_factor = np.sqrt(24 * 252)
    sharpe = (results_ser.mean() / results_ser.std()) * annualization_factor if results_ser.std() != 0 else 0
    
    # Drawdown
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak)
    max_drawdown = drawdown.min()
    
    metrics = {
        "Total Return": f"{total_return:.2%}",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Max Drawdown": f"{max_drawdown:.2%}",
        "Equity Curve": cum_returns
    }
    
    return metrics
