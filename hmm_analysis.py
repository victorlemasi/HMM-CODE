import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from config import HMM_COMPONENTS

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def detect_breakout(df: pd.DataFrame):
    """
    Fits an HMM to detect price regimes using BIC for optimal state selection.
    Features: Returns, Volatility, Range, Momentum, RSI, Vol/Vol Ratio.
    """
    df = df.copy()
    
    # 1. Feature Engineering
    df['Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Range'] = (df['High'] - df['Low']) / df['Close']
    df['Volatility'] = df['Returns'].rolling(window=10).std()
    df['Momentum'] = df['Returns'].rolling(window=5).mean() - df['Returns'].rolling(window=20).mean()
    df['RSI'] = calculate_rsi(df['Close'])
    
    # Volume/Volatility Ratio (Efficiency)
    if 'Volume' in df.columns:
        # Use a small epsilon to avoid division by zero
        df['Vol_Eff'] = df['Range'] / (df['Volume'].rolling(window=10).mean() + 1e-9)
    else:
        df['Vol_Eff'] = 0
        
    df = df.dropna()
    
    # Features for HMM
    features_cols = ['Returns', 'Volatility', 'Range', 'Momentum', 'RSI', 'Vol_Eff']
    features = df[features_cols].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # 2. Dynamic State Selection (BIC)
    best_bic = np.inf
    best_model = None
    best_n = 3
    
    for n in range(3, 6): # Try 3, 4, 5 states
        try:
            model = GaussianHMM(n_components=n, covariance_type="full", n_iter=1000, random_state=42)
            model.fit(features_scaled)
            bic = model.bic(features_scaled)
            if bic < best_bic:
                best_bic = bic
                best_model = model
                best_n = n
        except:
            continue
            
    if best_model is None:
        raise ValueError("Could not fit HMM model")

    model = best_model
    states = model.predict(features_scaled)
    
    # 3. Regime Mapping (Labeling)
    # Define "Breakout" as state with highest (Volatility + Range)
    state_metrics = []
    for i in range(best_n):
        mask = (states == i)
        # return_mean, vol_mean, range_mean
        metrics = {
            'id': i,
            'vol': features[mask, 1].mean(),
            'range': features[mask, 2].mean(),
            'ret': df['Returns'].values[mask].mean()
        }
        state_metrics.append(metrics)
    
    # Sort states by high-activity (Vol + Range)
    sorted_states = sorted(state_metrics, key=lambda x: x['vol'] + x['range'])
    
    # Map IDs to Labels
    # Lowest vol = Consolidation, Highest = Breakout, others = Normal/Trend
    labels = {}
    labels[sorted_states[0]['id']] = "Consolidation"
    labels[sorted_states[-1]['id']] = "Breakout"
    for i in range(1, best_n - 1):
        labels[sorted_states[i]['id']] = "Trend" if abs(sorted_states[i]['ret']) > 0.0001 else "Stable"

    current_state_id = states[-1]
    regime = labels[current_state_id]
    
    is_breakout = (regime == "Breakout")
    direction = "None"
    if is_breakout or regime == "Trend":
        avg_ret = labels_to_ret = [s['ret'] for s in state_metrics if s['id'] == current_state_id][0]
        direction = "LONG" if avg_ret > 0 else "SHORT"
    
    hist_states = pd.Series(states, index=df.index)
    
    return is_breakout, direction, regime, current_state_id

if __name__ == "__main__":
    pass
