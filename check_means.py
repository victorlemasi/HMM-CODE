import pickle
import os
path = r"c:\Users\lenovo\Downloads\scanner\Currency-Pair-Scanner-Analysis\hmm_models\GBPUSD_hmm.pkl"
with open(path, 'rb') as f:
    data = pickle.load(f)
model = data['model']
print(f"Means (Feature 0 is Returns):")
for i, m in enumerate(model.means_):
    print(f"  State {i}: mean_ret={m[0]:.8f}, abs_mean={abs(m[0]):.8f}")
