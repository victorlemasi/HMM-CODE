import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from config import N_CLUSTERS

from sklearn.metrics import silhouette_score

def cluster_assets(returns_df: pd.DataFrame):
    """
    Groups assets using Hierarchical Clustering, optimizing N clusters via Silhouette Score.
    """
    corr = returns_df.corr()
    dist = 1 - corr
    
    best_n = 2
    best_score = -1
    best_labels = None
    
    # Try different cluster counts
    for n in range(2, 7): # Try 2 to 6 clusters
        clustering = AgglomerativeClustering(n_clusters=n, metric='precomputed', linkage='complete')
        labels = clustering.fit_predict(dist)
        
        # Silhouette score requires at least 2 clusters and samples
        score = silhouette_score(dist, labels, metric='precomputed')
        
        if score > best_score:
            best_score = score
            best_n = n
            best_labels = labels
            
    print(f"Optimal clusters found: {best_n} (Silhouette Score: {best_score:.3f})")
    
    cluster_mapping = pd.Series(best_labels, index=returns_df.columns, name='Cluster')
    
    return cluster_mapping, corr

def plot_clusters(corr: pd.DataFrame, cluster_mapping: pd.Series):
    """
    Visualizes the correlation matrix with cluster labels.
    """
    plt.figure(figsize=(12, 10))
    # Reorder columns by cluster
    sorted_pairs = cluster_mapping.sort_values().index
    sns.heatmap(corr.loc[sorted_pairs, sorted_pairs], annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Currency Pair Correlation (Clustered)")
    plt.savefig('correlation_clusters.png')
    plt.close()

if __name__ == "__main__":
    # Test with mockup data if needed
    pass
