import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from config import HMM_COMPONENTS, ASSET_MAPPINGS, COMMODITY_TICKERS, YIELD_TICKERS, ATR_THRESHOLD_MULTIPLIER

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(window=period).mean()

def detect_breakout(df: pd.DataFrame, ticker: str = None, macro_data: dict = None):
    """
    Fits an HMM to detect price regimes using BIC for optimal state selection.
    Features: Returns, Volatility, Range, Momentum, RSI, Vol/Vol Ratio.
    Asset-Specific Extras: Commodity Correlation or Yield levels.
    """
    df = df.copy()
    
    # 1. Feature Engineering
    df['Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Range'] = (df['High'] - df['Low']) / df['Close']
    df['Volatility'] = df['Returns'].rolling(window=10).std()
    df['Momentum'] = df['Returns'].rolling(window=5).mean() - df['Returns'].rolling(window=20).mean()
    df['RSI'] = calculate_rsi(df['Close'])
    df['ATR'] = calculate_atr(df)
    df['ATR_Norm'] = df['ATR'] / df['Close']
    
    # Volume/Volatility Ratio (Efficiency)
    if 'Volume' in df.columns:
        df['Vol_Eff'] = df['Range'] / (df['Volume'].rolling(window=10).mean() + 1e-9)
    else:
        df['Vol_Eff'] = 0
    
    features_cols = ['Returns', 'Volatility', 'Range', 'Momentum', 'RSI', 'Vol_Eff']

    # 1.1 Asset-Specific Features
    if ticker in ASSET_MAPPINGS and macro_data:
        mapping = ASSET_MAPPINGS[ticker]
        m_type = mapping['type']
        m_key = mapping['key']
        
        # "Clean-Join" Pattern: Standardize and align
        price_idx = df.index.tz_localize(None) if df.index.tz else df.index
        df.index = price_idx
        
        if m_type == 'commodity':
            com_ticker = COMMODITY_TICKERS.get(m_key)
            if com_ticker in macro_data:
                com_df = macro_data[com_ticker].copy()
                com_df.index = com_df.index.tz_localize(None) if com_df.index.tz else com_df.index
                
                # Align and map daily/sparse data to high-freq index
                com_df_aligned = com_df.reindex(price_idx, method='ffill').bfill()
                
                # Rolling correlation with commodity returns
                com_ret = np.log(com_df_aligned['Close'] / com_df_aligned['Close'].shift(1))
                df['Spec_Feat'] = com_ret.rolling(20).corr(df['Returns'])
                features_cols.append('Spec_Feat')
                
        elif m_type == 'yield':
            yield_ticker = YIELD_TICKERS.get(m_key)
            if yield_ticker in macro_data:
                yield_df = macro_data[yield_ticker].copy()
                yield_df.index = yield_df.index.tz_localize(None) if yield_df.index.tz else yield_df.index
                
                # Align and carry yields into FX session gaps
                yield_df_aligned = yield_df.reindex(price_idx, method='ffill').bfill()
                
                # Include absolute yield level
                df['Spec_Feat'] = yield_df_aligned['Close'] 
                features_cols.append('Spec_Feat')

    df = df.dropna()
    features = df[features_cols].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # 2. 3-State Model (User Request)
    best_n = 3
    try:
        # Use fixed 3 states as requested
        model = GaussianHMM(n_components=best_n, covariance_type="diag", n_iter=1000, tol=1e-2, random_state=42)
        model.fit(features_scaled)
    except Exception as e:
        raise ValueError(f"Could not fit HMM model: {e}")

    states = model.predict(features_scaled)
    
    # 3. Regime Mapping (Labeling)
    # Define "Breakout" as state with highest (Volatility + Range)
    state_metrics = []
    # Count occurrences of each state to avoid empty slices
    unique_states, counts = np.unique(states, return_counts=True)
    state_counts = dict(zip(unique_states, counts))

    for i in range(best_n):
        # Robustly handle states that might not have any predictions (unlikely but possible after fit)
        if i in state_counts and state_counts[i] > 0:
            mask = (states == i)
            metrics = {
                'id': i,
                'vol': features[mask, 1].mean(),
                'range': features[mask, 2].mean(),
                'ret': df['Returns'].values[mask].mean()
            }
        else:
            # Fallback for empty states to avoid runtime warnings
            metrics = {'id': i, 'vol': 0, 'range': 0, 'ret': 0}
            
        state_metrics.append(metrics)
    
    # Sort states by high-activity (Vol + Range)
    sorted_states = sorted(state_metrics, key=lambda x: x['vol'] + x['range'])
    
    # Map IDs to Labels
    # Lowest activity = Consolidation
    # Mid activity = Mean Reversion
    # Highest activity = Trend Breakout
    labels = {}
    labels[sorted_states[0]['id']] = "Consolidation"
    labels[sorted_states[1]['id']] = "Mean Reversion"
    labels[sorted_states[2]['id']] = "Trend Breakout"

    current_state_id = states[-1]
    regime = labels[current_state_id]
    # If the states are too close in 'Return' space, it's noise, not a regime
    if hasattr(model, "means_") and len(model.means_) >= 2:
        # We check the difference between 'Consolidation' and 'Trend Breakout' means
        mu_cons = [s['ret'] for s in state_metrics if labels[s['id']] == "Consolidation"][0]
        mu_break = [s['ret'] for s in state_metrics if labels[s['id']] == "Trend Breakout"][0]
        
        # Dynamic Threshold based on ATR
        current_atr_norm = df['ATR_Norm'].iloc[-1]
        mu_diff_threshold = current_atr_norm * ATR_THRESHOLD_MULTIPLIER
        
        mu_diff = abs(mu_break - mu_cons)
        if mu_diff < mu_diff_threshold:
            # Force regime to Consolidation if the "Breakout" isn't distinct enough
            regime = "Consolidation"
            is_breakout = False

    is_breakout = (regime == "Trend Breakout")
    direction = "None"
    if is_breakout or regime == "Mean Reversion":
        avg_ret = [s['ret'] for s in state_metrics if s['id'] == current_state_id][0]
        direction = "LONG" if avg_ret > 0 else "SHORT"
    
    hist_states = pd.Series(states, index=df.index)
    
    return is_breakout, direction, regime, current_state_id

if __name__ == "__main__":
    pass
