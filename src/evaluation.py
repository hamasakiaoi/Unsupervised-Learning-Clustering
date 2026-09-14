"""
Cluster Evaluation and Validation Metrics Module.

Implements Elbow analysis (WCSS), Silhouette Score, Calinski-Harabasz Index,
Davies-Bouldin Index, Bootstrap Stability Assessment, and Cross-Algorithm Agreement.
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import (
    silhouette_score,
    silhouette_samples,
    calinski_harabasz_score,
    davies_bouldin_score,
    adjusted_rand_score,
    normalized_mutual_info_score
)

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def evaluate_cluster_range(
    X: np.ndarray,
    k_min: int = 2,
    k_max: int = 8,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Evaluate K-Means across a candidate range of cluster counts k in [k_min, k_max].

    Returns DataFrame with:
        k: Number of clusters.
        Inertia: Within-Cluster Sum of Squares (WCSS).
        Silhouette: Mean silhouette coefficient.
        Calinski_Harabasz: Variance ratio criterion.
        Davies_Bouldin: Cluster separation ratio (lower is better).
    """
    results = []
    print(f"[EVAL] Evaluating K-Means candidate cluster counts from k={k_min} to k={k_max} ...")

    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, init="k-means++", n_init=15, max_iter=300, random_state=random_state)
        labels = km.fit_predict(X)

        inertia = km.inertia_
        sil = silhouette_score(X, labels)
        ch = calinski_harabasz_score(X, labels)
        db = davies_bouldin_score(X, labels)

        results.append({
            "k": k,
            "Inertia": inertia,
            "Silhouette": sil,
            "Calinski_Harabasz": ch,
            "Davies_Bouldin": db
        })
        print(f"  k={k}: Silhouette={sil:.4f}, Calinski-Harabasz={ch:.1f}, Davies-Bouldin={db:.4f}, Inertia={inertia:.1f}")

    return pd.DataFrame(results)


def evaluate_hierarchical_range(
    X: np.ndarray,
    k_min: int = 2,
    k_max: int = 8,
    linkage_method: str = "ward"
) -> pd.DataFrame:
    """
    Evaluate Agglomerative Hierarchical Clustering across candidate k in [k_min, k_max].
    """
    results = []
    print(f"[EVAL] Evaluating Hierarchical Clustering (linkage='{linkage_method}') from k={k_min} to k={k_max} ...")

    for k in range(k_min, k_max + 1):
        hc = AgglomerativeClustering(n_clusters=k, metric="euclidean", linkage=linkage_method)
        labels = hc.fit_predict(X)

        sil = silhouette_score(X, labels)
        ch = calinski_harabasz_score(X, labels)
        db = davies_bouldin_score(X, labels)

        results.append({
            "k": k,
            "Silhouette": sil,
            "Calinski_Harabasz": ch,
            "Davies_Bouldin": db
        })
        print(f"  Hierarchical k={k}: Silhouette={sil:.4f}, Calinski-Harabasz={ch:.1f}, Davies-Bouldin={db:.4f}")

    return pd.DataFrame(results)


def evaluate_stability(
    X: np.ndarray,
    n_clusters: int,
    n_bootstraps: int = 10,
    sample_fraction: float = 0.8,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Assess clustering stability using bootstrap resampling and Adjusted Rand Index (ARI).
    Fits baseline model on full dataset, then resamples sample_fraction of the data
    without replacement, refits, and computes ARI on the overlapping subset.
    """
    print(f"[EVAL] Running bootstrap stability test (n_bootstraps={n_bootstraps}, fraction={sample_fraction}) for k={n_clusters}...")
    rng = np.random.default_rng(random_state)
    n_samples = len(X)
    sub_size = int(n_samples * sample_fraction)

    base_km = KMeans(n_clusters=n_clusters, init="k-means++", n_init=10, random_state=random_state)
    base_labels = base_km.fit_predict(X)

    ari_scores = []
    for i in range(n_bootstraps):
        sub_indices = rng.choice(n_samples, size=sub_size, replace=False)
        X_sub = X[sub_indices]
        
        sub_km = KMeans(n_clusters=n_clusters, init="k-means++", n_init=10, random_state=random_state + i + 1)
        sub_labels = sub_km.fit_predict(X_sub)
        
        ari = adjusted_rand_score(base_labels[sub_indices], sub_labels)
        ari_scores.append(ari)

    mean_ari = float(np.mean(ari_scores))
    std_ari = float(np.std(ari_scores))
    min_ari = float(np.min(ari_scores))
    max_ari = float(np.max(ari_scores))

    print(f"[EVAL] Stability ARI: Mean={mean_ari:.4f} +/- {std_ari:.4f} (Min={min_ari:.4f}, Max={max_ari:.4f})")
    return {
        "mean_ari": mean_ari,
        "std_ari": std_ari,
        "min_ari": min_ari,
        "max_ari": max_ari,
        "all_ari_scores": ari_scores
    }


def compare_algorithms(
    labels_kmeans: np.ndarray,
    labels_hierarchical: np.ndarray
) -> Dict[str, float]:
    """
    Compute mutual agreement between K-Means and Hierarchical Clustering assignments.
    """
    ari = float(adjusted_rand_score(labels_kmeans, labels_hierarchical))
    nmi = float(normalized_mutual_info_score(labels_kmeans, labels_hierarchical))
    print(f"[EVAL] Cross-Algorithm Consensus: Adjusted Rand Index (ARI) = {ari:.4f}, NMI = {nmi:.4f}")
    return {"ari": ari, "nmi": nmi}


def get_silhouette_samples_data(X: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Return array of silhouette coefficients for individual observations."""
    return silhouette_samples(X, labels)
