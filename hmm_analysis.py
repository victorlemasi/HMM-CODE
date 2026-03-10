import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from config import HMM_COMPONENTS

def detect_breakout(df: pd.DataFrame):
    """
    Fits an HMM to detect price regimes based on returns and volatility.
    """
    # Feature Engineering
    df = df.copy()
    df['Returns'] = df['Close'].pct_change()
    df['Range'] = (df['High'] - df['Low']) / df['Close']
    df['Volatility'] = df['Returns'].rolling(window=20).std()
    
    df = df.dropna()
    
    # Features for HMM
    features = df[['Returns', 'Volatility', 'Range']].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Model Setup
    model = GaussianHMM(n_components=HMM_COMPONENTS, covariance_type="full", n_iter=1000)
    model.fit(features_scaled)
    
    # Predict states
    states = model.predict(features_scaled)
    
    # Identify the "Breakout" state
    # We define it as the state with the highest mean Volatility OR highest mean Range
    state_means = []
    for i in range(HMM_COMPONENTS):
        state_means.append(features[states == i].mean(axis=0))
    
    state_means = np.array(state_means)
    # Volatility is index 1, Range is index 2
    breakout_state = np.argmax(state_means[:, 1] + state_means[:, 2])
    
    current_state = states[-1]
    is_breakout = (current_state == breakout_state)
    
    return is_breakout, states, breakout_state

if __name__ == "__main__":
    pass
