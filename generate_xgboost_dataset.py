import pandas as pd
import numpy as np
import joblib
import os
import pickle
from data_fetcher import fetch_data, get_macro_data
from hmm_analysis import prepare_hmm_features, calculate_atr
from config import CURRENCY_PAIRS, HMM_MODELS_PATH

def generate_dataset():
    """
    Phase 5: Hybrid AI Ensembling.
    Re-runs the fitted HMM across historical data to pair the Unsupervised State
    predictions with Supervised Forward Returns.
    """
    print("Generating XGBoost Training Matrix...")
    
    # We need a large sample. Yahoo 1h data goes back 730 days max.
    data = fetch_data(CURRENCY_PAIRS, interval='1h', period='700d')
    macro_data = get_macro_data(interval='1h', period='700d')
    
    all_rows = []
    
    for ticker, df in data.items():
        if df.empty or len(df) < 100:
            continue
            
        print(f"Processing {ticker} for XGBoost Dataset...")
        
        # 1. Prepare Features
        features = prepare_hmm_features(df, ticker, macro_data)
        if features is None or len(features) < 100:
            continue
            
        # 2. Load Model
        model_name = f"{ticker.replace('=X', '').replace('=F', '')}_hmm.pkl"
        model_path = os.path.join(HMM_MODELS_PATH, model_name)
        if not os.path.exists(model_path):
            continue
            
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                hmm_model = model_data['model']
                scaler = model_data['scaler']
        except Exception as e:
            print(f"Failed to load {ticker}: {e}")
            continue
            
        # 3. Predict States and Probabilities
        features_scaled = scaler.transform(features)
        try:
            states = hmm_model.predict(features_scaled)
            probs = hmm_model.predict_proba(features_scaled)
        except Exception:
            continue
            
        # 4. Calculate Forward Returns (24-hour lookahead)
        # We shift the close price negatively by 24 to get the future price
        close_prices = df['Close'].iloc[-len(features):]
        forward_24h_return = (close_prices.shift(-24) - close_prices) / close_prices
        
        atrs = calculate_atr(df).iloc[-len(features):]
        
        # Determine success label: 1 if Forward Return > 0.5 * ATR (percent) else 0
        # Wait, ATR is absolute points, return is percentage. 
        # So we compare absolute forward yield to ATR.
        forward_24h_pts = close_prices.shift(-24) - close_prices
        labels_long = (forward_24h_pts > (0.5 * atrs)).astype(int)
        labels_short = (forward_24h_pts < (-0.5 * atrs)).astype(int)
        
        # For simplicity in this engine, we will map standard metrics
        for i in range(len(features) - 24): # Skip last 24 rows which have no forward return
            # Extract the raw state features to feed XGBoost
            state_id = states[i]
            max_prob = np.max(probs[i])
            
            # The XGBoost model needs to know if the HMM predicted Long or Short implicitly.
            # We don't have the full regime matrix logic mapped here, so we just pass the Raw State.
            
            row = {
                'state_id': state_id,
                'hmm_confidence': max_prob,
                'atr_normalized': atrs.iloc[i] / close_prices.iloc[i],
                'target_long_win': labels_long.iloc[i],
                'target_short_win': labels_short.iloc[i]
            }
                
            all_rows.append(row)
            
    # Combine and save
    final_df = pd.DataFrame(all_rows)
    final_df.to_csv("xgboost_training_matrix.csv", index=False)
    print(f"Dataset saved! Shape: {final_df.shape}")

if __name__ == "__main__":
    generate_dataset()
