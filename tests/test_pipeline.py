"""
Automated Test Suite for Clustering Analysis Pipeline.

Validates data loading, preprocessing transformations, clustering algorithms,
evaluation metric computations, dimensionality reduction, stability assessment,
and visualization asset generation.

Compatible with both standard Python `unittest` and `pytest`.
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_loading import load_raw_data, get_project_root
from src.preprocessing import (
    clean_transactions,
    engineer_customer_features,
    prepare_clustering_matrix,
    save_processed_data,
    CORE_FEATURES
)
from src.clustering import (
    train_kmeans,
    train_hierarchical,
    compute_hierarchical_linkage,
    compute_pca,
    compute_tsne
)
from src.evaluation import (
    evaluate_cluster_range,
    evaluate_stability,
    compare_algorithms
)


def _ensure_processed_prerequisites():
    """Ensure processed data files exist so tests can execute in any environment."""
    cust_path = os.path.join(PROJECT_ROOT, "data", "processed", "customer_features.csv")
    scaled_path = os.path.join(PROJECT_ROOT, "data", "processed", "scaled_features.csv")
    
    if not os.path.exists(cust_path) or not os.path.exists(scaled_path):
        df_raw = load_raw_data()
        purchases, cancellations = clean_transactions(df_raw)
        df_cust = engineer_customer_features(purchases, cancellations)
        _, _, X_scaled, _ = prepare_clustering_matrix(df_cust, CORE_FEATURES)
        save_processed_data(df_cust, X_scaled, CORE_FEATURES)


class TestClusteringPipeline(unittest.TestCase):
    """Formal test case class discoverable by python -m unittest."""

    @classmethod
    def setUpClass(cls):
        _ensure_processed_prerequisites()

    def test_data_loading(self):
        """Verify raw dataset loads with expected shape and attributes."""
        df = load_raw_data()
        self.assertEqual(len(df), 541909)
        expected_cols = [
            "InvoiceNo", "StockCode", "Description", "Quantity",
            "InvoiceDate", "UnitPrice", "CustomerID", "Country"
        ]
        for col in expected_cols:
            self.assertIn(col, df.columns)

    def test_transaction_cleaning(self):
        """Verify cleaning filters out anonymous transactions and separates cancellations."""
        df = load_raw_data()
        purchases, cancellations = clean_transactions(df)
        
        self.assertGreater(len(purchases), 0)
        self.assertGreater(len(cancellations), 0)
        self.assertTrue((purchases['Quantity'] > 0).all())
        self.assertTrue((purchases['UnitPrice'] > 0).all())
        self.assertEqual(purchases['CustomerID'].isnull().sum(), 0)

    def test_customer_feature_engineering(self):
        """Verify customer behavioral feature aggregation."""
        df = load_raw_data()
        purchases, cancellations = clean_transactions(df)
        df_cust = engineer_customer_features(purchases, cancellations)

        self.assertEqual(len(df_cust), 4334)
        for feat in CORE_FEATURES:
            self.assertIn(feat, df_cust.columns)
            self.assertFalse(df_cust[feat].isnull().any())
            self.assertTrue(np.isfinite(df_cust[feat]).all())

    def test_log1p_and_scaling(self):
        """Verify log1p transformation reduces skewness and standard scaling centers data."""
        cust_path = os.path.join(PROJECT_ROOT, "data", "processed", "customer_features.csv")
        df_cust = pd.read_csv(cust_path)
        X_raw, X_log, X_scaled, scaler = prepare_clustering_matrix(df_cust, CORE_FEATURES)

        self.assertEqual(X_scaled.shape, (len(df_cust), len(CORE_FEATURES)))
        self.assertTrue(np.allclose(X_scaled.mean(axis=0), 0.0, atol=1e-5))
        self.assertTrue(np.allclose(X_scaled.std(axis=0), 1.0, atol=1e-5))
        
        # Check that Monetary raw skew > log skew
        self.assertGreater(X_raw['Monetary'].skew(), X_log['Monetary_log'].skew())

    def test_kmeans_model(self):
        """Verify K-Means produces valid clusters and centroids."""
        scaled_path = os.path.join(PROJECT_ROOT, "data", "processed", "scaled_features.csv")
        scaled_df = pd.read_csv(scaled_path)
        feature_cols = [c for c in scaled_df.columns if c != "CustomerID"]
        X = scaled_df[feature_cols].values

        km, labels = train_kmeans(X, n_clusters=4, random_state=42)
        self.assertEqual(len(labels), len(X))
        self.assertEqual(len(np.unique(labels)), 4)
        self.assertGreater(km.inertia_, 0)
        self.assertEqual(km.cluster_centers_.shape, (4, len(feature_cols)))

    def test_hierarchical_clustering(self):
        """Verify Agglomerative Hierarchical clustering and linkage computation."""
        scaled_path = os.path.join(PROJECT_ROOT, "data", "processed", "scaled_features.csv")
        scaled_df = pd.read_csv(scaled_path)
        feature_cols = [c for c in scaled_df.columns if c != "CustomerID"]
        X = scaled_df[feature_cols].values

        hc_model, hc_labels = train_hierarchical(X, n_clusters=4, linkage_method="ward")
        self.assertEqual(len(hc_labels), len(X))
        self.assertEqual(len(np.unique(hc_labels)), 4)

        Z, sample_idx = compute_hierarchical_linkage(X, sample_size=500, linkage_method="ward", random_state=42)
        self.assertEqual(len(sample_idx), 500)
        self.assertEqual(Z.shape, (499, 4))

    def test_pca_decomposition(self):
        """Verify PCA returns proper 2D projection and explained variance."""
        scaled_path = os.path.join(PROJECT_ROOT, "data", "processed", "scaled_features.csv")
        scaled_df = pd.read_csv(scaled_path)
        feature_cols = [c for c in scaled_df.columns if c != "CustomerID"]
        X = scaled_df[feature_cols].values

        pca, X_pca, loadings = compute_pca(X, n_components=2, feature_names=feature_cols)
        self.assertEqual(X_pca.shape, (len(X), 2))
        self.assertEqual(len(pca.explained_variance_ratio_), 2)
        self.assertGreater(pca.explained_variance_ratio_.sum(), 0.65)  # Explains >65% of total variance
        self.assertEqual(loadings.shape, (len(feature_cols), 2))

    def test_stability_and_metrics(self):
        """Verify stability evaluation and cluster range metric computation."""
        scaled_path = os.path.join(PROJECT_ROOT, "data", "processed", "scaled_features.csv")
        scaled_df = pd.read_csv(scaled_path)
        feature_cols = [c for c in scaled_df.columns if c != "CustomerID"]
        X_sub = scaled_df[feature_cols].values[:300]  # Subsample for test execution speed

        # Test stability bootstrap
        stability = evaluate_stability(X_sub, n_clusters=4, n_bootstraps=3, sample_fraction=0.8, random_state=42)
        self.assertIn("mean_ari", stability)
        self.assertGreater(stability["mean_ari"], 0.7)

        # Test algorithm agreement
        km, km_labels = train_kmeans(X_sub, n_clusters=4, random_state=42)
        hc, hc_labels = train_hierarchical(X_sub, n_clusters=4, linkage_method="ward")
        consensus = compare_algorithms(km_labels, hc_labels)
        self.assertIn("ari", consensus)
        self.assertIn("nmi", consensus)

    def test_visualizations_generated(self):
        """Verify all required visualization PNG assets exist and are non-empty."""
        required_figures = [
            "visualizations/01_raw_vs_log_distributions.png",
            "visualizations/02_feature_correlation_heatmap.png",
            "visualizations/03_cluster_evaluation_metrics.png",
            "visualizations/04_hierarchical_dendrogram.png",
            "visualizations/05_silhouette_analysis.png",
            "visualizations/06_pca_2d_projection.png",
            "visualizations/07_tsne_manifold_projection.png",
            "visualizations/08_cluster_radar_profiles.png",
            "visualizations/09_cluster_boxplots_metrics.png",
            "visualizations/10_revenue_contribution_and_sizes.png"
        ]
        for rel_path in required_figures:
            fig_path = os.path.join(PROJECT_ROOT, rel_path)
            self.assertTrue(os.path.exists(fig_path), f"Missing figure: {fig_path}")
            self.assertGreater(os.path.getsize(fig_path), 10000, f"Figure too small / empty: {fig_path}")


# Standalone function interfaces for pytest and backward compatibility
def test_data_loading():
    TestClusteringPipeline().test_data_loading()

def test_transaction_cleaning():
    TestClusteringPipeline().test_transaction_cleaning()

def test_customer_feature_engineering():
    TestClusteringPipeline().test_customer_feature_engineering()

def test_log1p_and_scaling():
    _ensure_processed_prerequisites()
    TestClusteringPipeline().test_log1p_and_scaling()

def test_kmeans_model():
    _ensure_processed_prerequisites()
    TestClusteringPipeline().test_kmeans_model()

def test_hierarchical_clustering():
    _ensure_processed_prerequisites()
    TestClusteringPipeline().test_hierarchical_clustering()

def test_pca_decomposition():
    _ensure_processed_prerequisites()
    TestClusteringPipeline().test_pca_decomposition()

def test_stability_and_metrics():
    _ensure_processed_prerequisites()
    TestClusteringPipeline().test_stability_and_metrics()

def test_visualizations_generated():
    TestClusteringPipeline().test_visualizations_generated()


if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING AUTOMATED TEST SUITE FOR CLUSTERING ANALYSIS PIPELINE")
    print("=" * 80)
    unittest.main(verbosity=2)
