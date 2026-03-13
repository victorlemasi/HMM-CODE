import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from config import HMM_COMPONENTS, ASSET_MAPPINGS, COMMODITY_TICKERS, YIELD_TICKERS, ATR_MULTIPLIER_FX, ATR_MULTIPLIER_GOLD

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

def detect_breakout(df: pd.DataFrame, ticker: str = None, macro_data: dict = None, model=None):
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
    
    # 1.2 "Goldilocks" Window: Use 1,000 - 1,200 bars to avoid overfitting
    # 70 days of 1h data is ~1680 bars, we trim to most recent 1200 for fitting
    max_fit_bars = 1200
    if len(df) > max_fit_bars:
        df = df.iloc[-max_fit_bars:]
        
    features = df[features_cols].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # 2. 3-State HMM (Daily Retraining logic: fit if model not provided)
    best_n = 3
    if model is None:
        try:
            model = GaussianHMM(
                n_components=best_n, covariance_type="diag",
                n_iter=1000, tol=1e-2, random_state=42
            )
            model.fit(features_scaled)
        except Exception as e:
            raise ValueError(f"Could not fit HMM model: {e}")
    else:
        # If model provided (e.g. from a cache), we just use it
        pass

    states = model.predict(features_scaled)
    # Convert to plain Python ints throughout to avoid numpy hashability issues
    states = [int(s) for s in states]
    current_state_id = states[-1]

    # 3. Regime Labeling via KMeans "Hard Boundary" approach
    # Run KMeans on the full feature space to find 3 decisive cluster centers
    km = KMeans(n_clusters=best_n, random_state=42, n_init=10)
    km.fit(features_scaled)
    # Assign each HMM state to the nearest KMeans cluster center
    # by matching HMM means_ to KMeans centers
    from sklearn.metrics import pairwise_distances
    dist_matrix = pairwise_distances(model.means_, km.cluster_centers_)
    hmm_to_km = np.argmin(dist_matrix, axis=1)   # which KMeans cluster each HMM state maps to

    # Rank KMeans clusters by total variance in feature space → activity level
    km_variances = np.zeros(best_n)
    km_labels = km.predict(features_scaled)
    for k in range(best_n):
        mask = (km_labels == k)
        if mask.sum() > 0:
            km_variances[k] = features_scaled[mask].var(axis=0).sum()

    # Sort KMeans clusters: low variance = Consolidation, high = Trend Breakout
    km_sorted = np.argsort(km_variances)   # [lowest_var_cluster, mid, highest]
    km_rank = {int(km_sorted[0]): "Consolidation",
               int(km_sorted[1]): "Mean Reversion",
               int(km_sorted[2]): "Trend Breakout"}

    # Build final label map: HMM state → regime string (via KMeans cluster)
    labels = {int(i): km_rank[int(hmm_to_km[i])] for i in range(best_n)}

    # Build per-state return metrics for direction
    state_metrics = {}
    states_arr = np.array(states)
    for i in range(best_n):
        mask = (states_arr == i)
        state_metrics[i] = {
            'ret': float(df['Returns'].values[mask].mean()) if mask.sum() > 0 else 0.0
        }

    regime = labels[current_state_id]

    # 4. Statistical Separation Guard — dynamic ATR-based
    # Only reject a Trend Breakout if its return separation from Consolidation is too small
    if regime == "Trend Breakout":
        cons_id = [k for k, v in labels.items() if v == "Consolidation"][0]
        break_id = current_state_id
        mu_cons = state_metrics[cons_id]['ret']
        mu_break = state_metrics[break_id]['ret']
        current_atr_norm = float(df['ATR_Norm'].iloc[-1])
        
        # Determine multiplier (K) based on asset type
        # In this bot, tickers like 'GC=F' or 'CL=F' are commodities, others are FX
        is_commodity = ticker in ['GC=F', 'CL=F'] or ('=F' in str(ticker))
        k = ATR_MULTIPLIER_GOLD if is_commodity else ATR_MULTIPLIER_FX
        
        mu_diff_threshold = current_atr_norm * k
        if abs(mu_break - mu_cons) < mu_diff_threshold:
            regime = "Consolidation"

    is_breakout = (regime == "Trend Breakout")
    direction = "None"
    if is_breakout or regime == "Mean Reversion":
        avg_ret = state_metrics[current_state_id]['ret']
        direction = "LONG" if avg_ret > 0 else "SHORT"
    
    return is_breakout, direction, regime, current_state_id

def get_dynamic_exit_levels(regime, price, atr, direction):
    """
    State-based Exit Strategy (ATR-keyed):
    - Mean Reversion: Aim for 1.0x ATR profit with 1.5x ATR stop buffer.
    - Trend Breakout: Aim for 3.0x ATR 'Big Move' with tight 1.0x ATR stop.
    """
    if regime == "Mean Reversion":
        tp_dist = atr * 1.0
        sl_dist = atr * 1.5
    elif regime == "Trend Breakout":
        tp_dist = atr * 3.0
        sl_dist = atr * 1.0
    else:
        return None, None

    if direction == "LONG":
        tp = price + tp_dist
        sl = price - sl_dist
    elif direction == "SHORT":
        tp = price - tp_dist
        sl = price + sl_dist
    else:
        return None, None
        
    return float(tp), float(sl)

if __name__ == "__main__":
    pass
