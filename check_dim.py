import pickle
import os
path = r"c:\Users\lenovo\Downloads\scanner\Currency-Pair-Scanner-Analysis\hmm_models\EURUSD_hmm.pkl"
with open(path, 'rb') as f:
    data = pickle.load(f)
print(f"Model n_features: {data['model'].n_features}")
print(f"Scaler features count: {data['scaler'].n_features_in_}")
