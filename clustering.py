import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from config import N_CLUSTERS

def cluster_assets(returns_df: pd.DataFrame):
    """
    Groups assets using Hierarchical Clustering based on correlation.
    """
    # Use correlation as distance metric
    corr = returns_df.corr()
    
    # Hierarchical Clustering
    # We use 1 - correlation as the distance matrix
    dist = 1 - corr
    
    clustering = AgglomerativeClustering(n_clusters=N_CLUSTERS, metric='precomputed', linkage='complete')
    clusters = clustering.fit_predict(dist)
    
    # Store results
    cluster_mapping = pd.Series(clusters, index=returns_df.columns, name='Cluster')
    
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
