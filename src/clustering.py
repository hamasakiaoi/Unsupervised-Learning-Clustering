"""
Clustering Algorithms and Dimensionality Reduction Module.

Implements K-Means (with K-Means++ initialization), Agglomerative Hierarchical
Clustering (Ward's linkage), PCA, and t-SNE dimensionality reduction.
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from scipy.cluster.hierarchy import linkage

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def train_kmeans(
    X: np.ndarray,
    n_clusters: int,
    random_state: int = 42
) -> Tuple[KMeans, np.ndarray]:
    """
    Train K-Means clustering model using K-Means++ initialization.

    Args:
        X: Scaled feature matrix of shape (n_samples, n_features).
        n_clusters: Number of target clusters (k).
        random_state: Random seed for deterministic reproducibility.

    Returns:
        model: Fitted KMeans instance.
        labels: Cluster assignment array of shape (n_samples,).
    """
    model = KMeans(
        n_clusters=n_clusters,
        init="k-means++",
        n_init=15,
        max_iter=300,
        random_state=random_state
    )
    labels = model.fit_predict(X)
    return model, labels


def train_hierarchical(
    X: np.ndarray,
    n_clusters: int,
    linkage_method: str = "ward"
) -> Tuple[AgglomerativeClustering, np.ndarray]:
    """
    Train Agglomerative Hierarchical Clustering model.

    Args:
        X: Scaled feature matrix.
        n_clusters: Number of clusters cut from the dendrogram.
        linkage_method: Linkage criterion ('ward', 'complete', 'average').

    Returns:
        model: Fitted AgglomerativeClustering instance.
        labels: Cluster assignment array.
    """
    metric = "euclidean" if linkage_method == "ward" else "euclidean"
    model = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric=metric,
        linkage=linkage_method
    )
    labels = model.fit_predict(X)
    return model, labels


def compute_hierarchical_linkage(
    X: np.ndarray,
    sample_size: int = 1000,
    linkage_method: str = "ward",
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute hierarchical clustering linkage matrix for dendrogram visualization.
    Uses representative random sub-sampling for visual clarity when n_samples is large.

    Returns:
        Z (np.ndarray): Scipy linkage matrix.
        sample_indices (np.ndarray): Indices of sampled rows.
    """
    if len(X) > sample_size:
        rng = np.random.default_rng(random_state)
        sample_indices = rng.choice(len(X), size=sample_size, replace=False)
        X_sub = X[sample_indices]
    else:
        sample_indices = np.arange(len(X))
        X_sub = X

    Z = linkage(X_sub, method=linkage_method, metric="euclidean")
    return Z, sample_indices


def compute_pca(
    X: np.ndarray,
    n_components: int = 2,
    feature_names: Optional[list] = None,
    random_state: int = 42
) -> Tuple[PCA, np.ndarray, pd.DataFrame]:
    """
    Perform Principal Component Analysis for dimensional reduction and visualization.

    Returns:
        pca: Fitted PCA instance.
        X_pca: 2D projection array (n_samples, n_components).
        loadings_df: DataFrame of component loadings per feature.
    """
    pca = PCA(n_components=n_components, random_state=random_state)
    X_pca = pca.fit_transform(X)

    if feature_names is not None:
        loadings_df = pd.DataFrame(
            pca.components_.T,
            columns=[f"PC{i+1}" for i in range(n_components)],
            index=feature_names
        )
    else:
        loadings_df = pd.DataFrame(
            pca.components_.T,
            columns=[f"PC{i+1}" for i in range(n_components)]
        )

    return pca, X_pca, loadings_df


def compute_tsne(
    X: np.ndarray,
    n_components: int = 2,
    perplexity: float = 35.0,
    random_state: int = 42
) -> np.ndarray:
    """
    Perform t-SNE non-linear projection for 2D manifold visualization.
    """
    tsne = TSNE(
        n_components=n_components,
        perplexity=perplexity,
        learning_rate="auto",
        init="pca",
        max_iter=1000,
        random_state=random_state
    )
    X_tsne = tsne.fit_transform(X)
    return X_tsne
