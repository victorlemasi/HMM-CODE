import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_xgboost_hybrid():
    """
    Phase 5: Hybrid AI Ensembling.
    Trains an XGBoost gradient boosting classifier on the historically predicted 
    HMM state parameters to predict true forward breakouts.
    """
    print("Loading HMM Training Matrix...")
    try:
        df = pd.read_csv("xgboost_training_matrix.csv")
    except FileNotFoundError:
        print("Error: xgboost_training_matrix.csv not found. Run generate_xgboost_dataset.py first.")
        return
        
    print(f"Matrix loaded. Total Historical HMM Samples: {len(df)}")
    
    # We will build a unified classification target: 
    # Did the state yield a definitive breakout (either Long OR Short)?
    # 1 = True Breakout (Volatility Expansion), 0 = Chop/Trap
    
    y = df['target_long_win'] | df['target_short_win']
    
    # Features: Ticker, State ID, Max HMM Confidence, ATR, and specific Component Probabilities
    # We drop the targets
    X = df.drop(columns=['target_long_win', 'target_short_win'])
    
    print("Splitting train/test data...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("--- XGBOOST HYBRID ENSEMBLE RESULTS ---")
    print(f"Accuracy: {accuracy * 100:.2f}%")
    print(classification_report(y_test, y_pred))
    
    # Save Model
    joblib.dump(model, "xgb_breakout_filter.pkl")
    print("Saved XGBoost model to 'xgb_breakout_filter.pkl'")

if __name__ == "__main__":
    train_xgboost_hybrid()
