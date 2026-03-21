import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any

def diversify_signals(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures only one asset per cluster is picked if multiple show BREAKOUT.
    """
    col = 'Regime' if 'Regime' in summary.columns else 'State'
    breakouts: pd.DataFrame = summary[summary[col] == 'Trend Breakout'].copy()
    
    # Group by cluster and pick the first one
    diversified = breakouts.groupby('Cluster').head(1)
    
    return diversified

def get_exit_recommendations(summary: pd.DataFrame) -> List[str]:
    """
    Identifies assets that should be exited because they have left a 
    high-convictions regime.
    """
    col = 'Regime' if 'Regime' in summary.columns else 'State'
    exit_list = summary[~summary[col].isin(['Trend Breakout', 'Mean Reversion'])].index.tolist()
    return exit_list

def find_correlation_hedges(summary: pd.DataFrame) -> List[Dict]:
    """
    Identifies 'Market Neutral' opportunities where different clusters 
    are breaking out in opposite directions.
    """
    col = 'Regime' if 'Regime' in summary.columns else 'State'
    breakouts: pd.DataFrame = summary[summary[col] == 'Trend Breakout'].copy()
    if breakouts.empty:
        return []

    hedges = []
    clusters: List[Any] = list(breakouts['Cluster'].unique())
    
    for c1 in clusters:
        for c2 in clusters:
            if c1 == c2:
                continue
            
            assets1 = breakouts.loc[breakouts['Cluster'] == c1]
            assets2 = breakouts.loc[breakouts['Cluster'] == c2]
            
            for a1_idx, a1_row in assets1.iterrows():
                for a2_idx, a2_row in assets2.iterrows():
                    # If they move in opposite directions, it's a hedge
                    if a1_row['Direction'] != a2_row['Direction']:
                        hedges.append({
                            'Pair_A': a1_idx,
                            'Cluster_A': c1,
                            'Dir_A': a1_row['Direction'],
                            'Pair_B': a2_idx,
                            'Cluster_B': c2,
                            'Dir_B': a2_row['Direction'],
                            'Type': 'Market Neutral Hedge'
                        })
    return hedges

def optimize_portfolio_weights(active_tickers: List[str], returns_df: pd.DataFrame, expected_returns: Dict[str, float] = None) -> Dict[str, float]:
    """
    Phase 4: Dynamic Portfolio Optimization (Mean-Variance Routing).
    Calculates the Markowitz Efficient Frontier weights for the active signals
    to maximize the portfolio Sharpe Ratio, actively penalizing highly correlated pair selections.
    """
    from scipy.optimize import minimize
    
    if not active_tickers or returns_df is None or returns_df.empty:
        return {}
        
    # Isolate the returns of only the active tickers
    available_tickers = [t for t in active_tickers if t in returns_df.columns]
    if not available_tickers:
        return {t: 1.0/len(active_tickers) for t in active_tickers} # Fallback to equal weight
        
    portfolio_returns = returns_df[available_tickers]
    cov_matrix = portfolio_returns.cov() * 252 # Annualized covariance
    
    # If expected_returns are not provided, we assume equal expected returns 
    # (effectively finding the Global Minimum Variance portfolio)
    if expected_returns is None:
        mu = np.array([0.05] * len(available_tickers)) 
    else:
        mu = np.array([expected_returns.get(t, 0.05) for t in available_tickers])
        
    num_assets = len(available_tickers)
    
    # Objective Function: Negative Sharpe Ratio
    def neg_sharpe(weights):
        port_return = np.sum(mu * weights)
        port_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = port_return / port_volatility if port_volatility != 0 else 0
        return -sharpe
        
    # Constraints: Weights sum to 1.0
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
    
    # Bounds: No shorting weights (0 to 1) for the allocation algorithm
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    
    # Initial guess: Equal weighting
    init_guess = num_assets * [1. / num_assets,]
    
    try:
        opt_results = minimize(neg_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        opt_weights = opt_results.x
        weight_dict = {available_tickers[i]: float(opt_weights[i]) for i in range(num_assets)}
        return weight_dict
    except Exception as e:
        print(f" [MPT ERROR] Optimizer failed: {e}")
        return {t: 1.0/len(active_tickers) for t in active_tickers}
