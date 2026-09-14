"""
Main Analysis Driver Script.

Executes the complete unsupervised clustering pipeline end-to-end:
data loading, cleaning, feature engineering, transformation, evaluation,
model training, validation, visualization generation, and cluster profiling.
"""

import os
import sys
import json
import numpy as np
import pandas as pd

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.data_loading import load_raw_data
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
    evaluate_hierarchical_range,
    evaluate_stability,
    compare_algorithms
)
from src.visualization import (
    plot_distributions_comparison,
    plot_correlation_matrix,
    plot_cluster_evaluation_metrics,
    plot_hierarchical_dendrogram,
    plot_silhouette_diagram,
    plot_pca_scatter,
    plot_tsne_scatter,
    plot_radar_profiles,
    plot_cluster_boxplots,
    plot_revenue_and_population_share
)


CLUSTER_PERSONAS = {
    0: "Low-Value / Churned Buyers",
    1: "Champions / Power Retailers",
    2: "At-Risk Bulk Buyers",
    3: "Active Regular Customers"
}


def run_full_pipeline():
    print("=" * 80)
    print("STARTING END-TO-END UNSUPERVISED CLUSTERING ANALYSIS PIPELINE")
    print("=" * 80)

    # 1. Ingestion
    df_raw = load_raw_data()

    # 2. Cleaning & Transaction Level Preprocessing
    purchases, cancellations = clean_transactions(df_raw)

    # 3. Customer Feature Engineering
    df_cust = engineer_customer_features(purchases, cancellations)

    # 4. Clustering Matrix Preparation (Log1p & Scaling)
    X_raw, X_log, X_scaled, scaler = prepare_clustering_matrix(df_cust, CORE_FEATURES, scale_method="standard")
    save_processed_data(df_cust, X_scaled, CORE_FEATURES)

    # 5. Visualizing Distributions & Correlations
    print("[PIPELINE] Generating distribution and correlation charts...")
    plot_distributions_comparison(X_raw, X_log, "visualizations/01_raw_vs_log_distributions.png")
    plot_correlation_matrix(df_cust[CORE_FEATURES], "visualizations/02_feature_correlation_heatmap.png")

    # 6. Candidate Cluster Count Evaluation (k = 2..7)
    metrics_km = evaluate_cluster_range(X_scaled, k_min=2, k_max=7, random_state=42)
    metrics_hc = evaluate_hierarchical_range(X_scaled, k_min=2, k_max=7, linkage_method="ward")
    plot_cluster_evaluation_metrics(metrics_km, "visualizations/03_cluster_evaluation_metrics.png")

    # 7. Hierarchical Clustering Dendrogram
    print("[PIPELINE] Computing hierarchical linkage and dendrogram...")
    Z, _ = compute_hierarchical_linkage(X_scaled, sample_size=1000, linkage_method="ward", random_state=42)
    plot_hierarchical_dendrogram(Z, "visualizations/04_hierarchical_dendrogram.png", cut_threshold=45.0)

    # 8. Model Fitting: Primary K-Means (k=4)
    print("[PIPELINE] Fitting final K-Means (k=4) model...")
    km_model, km_labels = train_kmeans(X_scaled, n_clusters=4, random_state=42)
    df_cust['Cluster'] = km_labels
    df_cust['Persona'] = df_cust['Cluster'].map(CLUSTER_PERSONAS)

    # Hierarchical comparison model
    _, hc_labels = train_hierarchical(X_scaled, n_clusters=4, linkage_method="ward")
    comp_metrics = compare_algorithms(km_labels, hc_labels)

    # 9. Stability Evaluation
    stability = evaluate_stability(X_scaled, n_clusters=4, n_bootstraps=10, sample_fraction=0.8, random_state=42)

    # 10. Dimensionality Reduction (PCA & t-SNE)
    print("[PIPELINE] Computing PCA and t-SNE projections...")
    pca_model, X_pca, loadings = compute_pca(X_scaled, n_components=2, feature_names=CORE_FEATURES, random_state=42)
    print(f"[PIPELINE] PCA Explained Variance: PC1={pca_model.explained_variance_ratio_[0]*100:.1f}%, PC2={pca_model.explained_variance_ratio_[1]*100:.1f}%")
    print("PCA Loadings:\n", loadings)

    X_tsne = compute_tsne(X_scaled, n_components=2, perplexity=35, random_state=42)

    # 11. Visualizations
    plot_silhouette_diagram(X_scaled, km_labels, CLUSTER_PERSONAS, "visualizations/05_silhouette_analysis.png")
    plot_pca_scatter(X_pca, km_labels, CLUSTER_PERSONAS, pca_model.explained_variance_ratio_, "visualizations/06_pca_2d_projection.png")
    plot_tsne_scatter(X_tsne, km_labels, CLUSTER_PERSONAS, "visualizations/07_tsne_manifold_projection.png")
    
    scaled_df = pd.DataFrame(X_scaled, columns=CORE_FEATURES)
    plot_radar_profiles(scaled_df, km_labels, CLUSTER_PERSONAS, CORE_FEATURES, "visualizations/08_cluster_radar_profiles.png")
    plot_cluster_boxplots(df_cust, CLUSTER_PERSONAS, "visualizations/09_cluster_boxplots_metrics.png")
    plot_revenue_and_population_share(df_cust, CLUSTER_PERSONAS, "visualizations/10_revenue_contribution_and_sizes.png")

    # 12. Detailed Statistical Profiling
    print("[PIPELINE] Computing detailed cluster profiling statistics...")
    profile_means = df_cust.groupby('Cluster')[CORE_FEATURES].mean().round(2)
    profile_medians = df_cust.groupby('Cluster')[CORE_FEATURES].median().round(2)
    profile_std = df_cust.groupby('Cluster')[CORE_FEATURES].std().round(2)

    # Revenue and size summary
    counts = df_cust['Cluster'].value_counts().sort_index()
    pop_pct = (counts / len(df_cust) * 100).round(2)
    total_rev = df_cust['Monetary'].sum()
    cluster_rev = df_cust.groupby('Cluster')['Monetary'].sum()
    rev_pct = (cluster_rev / total_rev * 100).round(2)

    profile_summary = pd.DataFrame({
        "Cluster_ID": list(range(4)),
        "Persona": [CLUSTER_PERSONAS[i] for i in range(4)],
        "Customer_Count": counts.values,
        "Population_Share_Pct": pop_pct.values,
        "Total_Revenue_GBP": cluster_rev.round(2).values,
        "Revenue_Share_Pct": rev_pct.values,
        "Median_Recency_Days": profile_medians['Recency'].values,
        "Median_Frequency_Orders": profile_medians['Frequency'].values,
        "Median_Monetary_GBP": profile_medians['Monetary'].values,
        "Median_AOV_GBP": profile_medians['AOV'].values,
        "Median_Basket_Size": profile_medians['AvgBasketSize'].values,
        "Median_Unique_SKUs": profile_medians['UniqueSKUs'].values,
        "Median_Tenure_Days": profile_medians['Tenure'].values
    })

    print("\n--- EXECUTIVE CLUSTER PROFILE SUMMARY ---")
    print(profile_summary.to_string(index=False))

    # Save summary tables to disk for documentation and report generation
    proc_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "processed")
    os.makedirs(proc_dir, exist_ok=True)
    profile_summary.to_csv(os.path.join(proc_dir, "cluster_profile_summary.csv"), index=False)
    profile_means.to_csv(os.path.join(proc_dir, "cluster_feature_means.csv"))
    profile_medians.to_csv(os.path.join(proc_dir, "cluster_feature_medians.csv"))
    metrics_km.to_csv(os.path.join(proc_dir, "kmeans_evaluation_metrics.csv"), index=False)
    metrics_hc.to_csv(os.path.join(proc_dir, "hierarchical_evaluation_metrics.csv"), index=False)
    loadings.to_csv(os.path.join(proc_dir, "pca_feature_loadings.csv"))

    # Save metadata dictionary
    run_meta = {
        "dataset": "UCI Online Retail",
        "total_customers": len(df_cust),
        "selected_k": 4,
        "primary_algorithm": "K-Means++",
        "comparative_algorithm": "Agglomerative Hierarchical (Ward)",
        "cross_algorithm_ari": comp_metrics['ari'],
        "cross_algorithm_nmi": comp_metrics['nmi'],
        "stability_mean_ari": stability['mean_ari'],
        "pca_variance_explained": {
            "PC1": float(pca_model.explained_variance_ratio_[0]),
            "PC2": float(pca_model.explained_variance_ratio_[1]),
            "Total_2D": float(np.sum(pca_model.explained_variance_ratio_))
        }
    }
    with open(os.path.join(proc_dir, "analysis_summary_metadata.json"), "w") as f:
        json.dump(run_meta, f, indent=2)

    print("=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY! All assets generated.")
    print("=" * 80)


if __name__ == "__main__":
    run_full_pipeline()
