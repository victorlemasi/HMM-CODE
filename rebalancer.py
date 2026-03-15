import pandas as pd
from typing import Dict, List, Tuple

def diversify_signals(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures only one asset per cluster is picked if multiple show BREAKOUT.
    Selection is based on 'State' (BREAKOUT) and then we pick the first one 
    in alphabetically sorted list or could be refined by volatility.
    """
    breakouts = summary[summary['State'] == 'Trend Breakout'].copy()
    
    # Group by cluster and pick the first one
    # This ensures diversification: only one position per correlated group.
    diversified = breakouts.groupby('Cluster').head(1)
    
    return diversified

def get_exit_recommendations(summary: pd.DataFrame) -> List[str]:
    """
    Identifies assets that should be exited because they have left a 
    high-convictions regime (e.g., no longer in Breakout or Trend).
    """
    # Assets NOT in Trend Breakout or Mean Reversion should be considered for exit
    exit_list = summary[~summary['State'].isin(['Trend Breakout', 'Mean Reversion'])].index.tolist()
    return exit_list

def find_correlation_hedges(summary: pd.DataFrame) -> List[Dict]:
    """
    Identifies 'Market Neutral' opportunities where different clusters 
    are breaking out in opposite directions.
    """
    breakouts = summary[summary['State'] == 'Trend Breakout'].copy()
    if breakouts.empty:
        return []

    hedges = []
    clusters = breakouts['Cluster'].unique()
    
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            c1 = clusters[i]
            c2 = clusters[j]
            
            assets1 = breakouts[breakouts['Cluster'] == c1]
            assets2 = breakouts[breakouts['Cluster'] == c2]
            
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
