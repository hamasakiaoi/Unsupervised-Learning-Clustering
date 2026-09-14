"""
Visualization Module for Clustering and Exploratory Data Analysis.

Generates publication-quality figures (300 DPI) for analytical exploration,
cluster validation, dimensional projection, and profile interpretation.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List, Dict
from scipy.cluster.hierarchy import dendrogram

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set global publication styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})

CLUSTER_COLORS = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd", "#8c564b"]
PALETTE = ["#2E86AB", "#D9534F", "#3BB273", "#E09F3E"]


def _resolve_viz_path(save_path: str) -> str:
    """Ensure visualization output path resolves relative to project root if relative."""
    if not os.path.isabs(save_path):
        from src.data_loading import get_project_root
        save_path = os.path.join(get_project_root(), save_path)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    return save_path


def plot_distributions_comparison(
    X_raw: pd.DataFrame,
    X_log: pd.DataFrame,
    save_path: str = "visualizations/01_raw_vs_log_distributions.png"
) -> None:
    """Compare raw heavily skewed distributions against log1p transformed distributions."""
    save_path = _resolve_viz_path(save_path)
    features = ['Recency', 'Frequency', 'Monetary', 'AvgBasketSize']
    fig, axes = plt.subplots(4, 2, figsize=(12, 12))
    fig.suptitle("Feature Distributions: Raw vs. Log1p-Transformed (Variance Stabilization)", fontsize=14, y=0.99)

    for i, col in enumerate(features):
        # Raw feature distribution
        ax_raw = axes[i, 0]
        sns.histplot(X_raw[col], kde=True, ax=ax_raw, color="#2E86AB", bins=30)
        raw_skew = X_raw[col].skew()
        ax_raw.set_title(f"Raw {col} (Skewness = {raw_skew:+.2f})", fontsize=11, fontweight="bold")
        ax_raw.set_xlabel(col)
        ax_raw.set_ylabel("Customer Count")

        # Log-transformed distribution
        ax_log = axes[i, 1]
        log_col = f"{col}_log" if f"{col}_log" in X_log.columns else col
        sns.histplot(X_log[log_col], kde=True, ax=ax_log, color="#3BB273", bins=30)
        log_skew = X_log[log_col].skew()
        ax_log.set_title(f"Log1p({col}) (Skewness = {log_skew:+.2f})", fontsize=11, fontweight="bold")
        ax_log.set_xlabel(f"log(1 + {col})")
        ax_log.set_ylabel("Customer Count")

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved distribution comparison to {save_path}")


def plot_correlation_matrix(
    df_features: pd.DataFrame,
    save_path: str = "visualizations/02_feature_correlation_heatmap.png"
) -> None:
    """Generate annotated heatmap of Pearson correlation coefficients."""
    save_path = _resolve_viz_path(save_path)
    corr = df_features.corr()
    plt.figure(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    sns.heatmap(
        corr,
        mask=mask,
        cmap=cmap,
        vmax=1.0,
        vmin=-0.5,
        center=0,
        annot=True,
        fmt=".2f",
        square=True,
        linewidths=0.7,
        cbar_kws={"shrink": 0.8, "label": "Pearson Correlation (r)"}
    )
    plt.title("Feature Correlation Matrix (Customer Behavioral Dimensions)", fontsize=13, pad=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved correlation matrix to {save_path}")


def plot_cluster_evaluation_metrics(
    metrics_df: pd.DataFrame,
    save_path: str = "visualizations/03_cluster_evaluation_metrics.png"
) -> None:
    """Plot 4-panel evaluation grid: Elbow WCSS, Silhouette, Calinski-Harabasz, Davies-Bouldin."""
    save_path = _resolve_viz_path(save_path)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Internal Cluster Validation Across Candidate Cluster Counts (k = 2 to 7)", fontsize=14, y=0.98)

    k_vals = metrics_df['k']

    # 1. Elbow WCSS
    ax1 = axes[0, 0]
    ax1.plot(k_vals, metrics_df['Inertia'], marker='o', color='#2E86AB', linewidth=2.2, markersize=7)
    ax1.axvline(x=4, color='#D9534F', linestyle='--', alpha=0.8, label="Selected k=4 (Elbow point)")
    ax1.set_title("Elbow Method: Within-Cluster Sum of Squares (Inertia)", fontweight="bold")
    ax1.set_xlabel("Number of Clusters (k)")
    ax1.set_ylabel("Inertia (WCSS)")
    ax1.legend()

    # 2. Silhouette Score
    ax2 = axes[0, 1]
    ax2.plot(k_vals, metrics_df['Silhouette'], marker='s', color='#3BB273', linewidth=2.2, markersize=7)
    ax2.axvline(x=4, color='#D9534F', linestyle='--', alpha=0.8, label="Selected k=4")
    ax2.set_title("Silhouette Score (Cluster Compactness & Separation)", fontweight="bold")
    ax2.set_xlabel("Number of Clusters (k)")
    ax2.set_ylabel("Mean Silhouette Coefficient")
    ax2.legend()

    # 3. Calinski-Harabasz
    ax3 = axes[1, 0]
    ax3.plot(k_vals, metrics_df['Calinski_Harabasz'], marker='^', color='#E09F3E', linewidth=2.2, markersize=7)
    ax3.axvline(x=4, color='#D9534F', linestyle='--', alpha=0.8, label="Selected k=4")
    ax3.set_title("Calinski-Harabasz Index (Variance Ratio Criterion)", fontweight="bold")
    ax3.set_xlabel("Number of Clusters (k)")
    ax3.set_ylabel("Calinski-Harabasz Score")
    ax3.legend()

    # 4. Davies-Bouldin
    ax4 = axes[1, 1]
    ax4.plot(k_vals, metrics_df['Davies_Bouldin'], marker='D', color='#8E44AD', linewidth=2.2, markersize=7)
    ax4.axvline(x=4, color='#D9534F', linestyle='--', alpha=0.8, label="Selected k=4 (Local Minimum)")
    ax4.set_title("Davies-Bouldin Index (Lower is Better)", fontweight="bold")
    ax4.set_xlabel("Number of Clusters (k)")
    ax4.set_ylabel("Davies-Bouldin Index")
    ax4.legend()

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved cluster evaluation grid to {save_path}")


def plot_hierarchical_dendrogram(
    linkage_matrix: np.ndarray,
    save_path: str = "visualizations/04_hierarchical_dendrogram.png",
    cut_threshold: Optional[float] = None
) -> None:
    """Plot truncated hierarchical clustering dendrogram using Ward's linkage."""
    save_path = _resolve_viz_path(save_path)
    plt.figure(figsize=(11, 6))
    dendrogram(
        linkage_matrix,
        truncate_mode="lastp",
        p=25,
        leaf_rotation=90,
        leaf_font_size=10,
        show_contracted=True,
        color_threshold=cut_threshold
    )
    if cut_threshold is not None:
        plt.axhline(y=cut_threshold, color="#D9534F", linestyle="--", linewidth=1.8, label=f"Cut Height = {cut_threshold:.1f} (k=4 clusters)")
        plt.legend(loc="upper right")

    plt.title("Hierarchical Clustering Dendrogram (Ward's Minimum Variance Criterion)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Cluster Node Index / Subtree (Truncated to Top 25 Branches)")
    plt.ylabel("Ward Linkage Distance (Euclidean Dissimilarity)")
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved hierarchical dendrogram to {save_path}")


def plot_silhouette_diagram(
    X: np.ndarray,
    labels: np.ndarray,
    cluster_names: Dict[int, str],
    save_path: str = "visualizations/05_silhouette_analysis.png"
) -> None:
    """Generate silhouette plot displaying per-cluster silhouette coefficient profiles."""
    from sklearn.metrics import silhouette_samples, silhouette_score

    save_path = _resolve_viz_path(save_path)
    sil_samples = silhouette_samples(X, labels)
    mean_sil = silhouette_score(X, labels)

    plt.figure(figsize=(9, 7))
    y_lower = 10

    unique_labels = sorted(np.unique(labels))
    for idx, cluster_id in enumerate(unique_labels):
        ith_cluster_sil = sil_samples[labels == cluster_id]
        ith_cluster_sil.sort()
        size_cluster_i = ith_cluster_sil.shape[0]
        y_upper = y_lower + size_cluster_i

        color = PALETTE[idx % len(PALETTE)]
        plt.fill_betweenx(
            np.arange(y_lower, y_upper),
            0,
            ith_cluster_sil,
            facecolor=color,
            edgecolor=color,
            alpha=0.75,
            label=f"{cluster_names.get(cluster_id, f'Cluster {cluster_id}')} (n={size_cluster_i})"
        )
        y_lower = y_upper + 10

    plt.axvline(x=mean_sil, color="#D9534F", linestyle="--", linewidth=2.0, label=f"Average Silhouette = {mean_sil:.3f}")
    plt.title("Silhouette Coefficient Profile by Cluster (k=4 Segmentation)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Silhouette Coefficient Values")
    plt.ylabel("Cluster Thickness (Observation Count)")
    plt.yticks([])
    plt.xlim([-0.2, 0.8])
    plt.legend(loc="upper right", frameon=True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved silhouette diagram to {save_path}")


def plot_pca_scatter(
    X_pca: np.ndarray,
    labels: np.ndarray,
    cluster_names: Dict[int, str],
    explained_var: np.ndarray,
    save_path: str = "visualizations/06_pca_2d_projection.png"
) -> None:
    """Plot 2D PCA projection of clusters with cluster centroids and variance ratios."""
    save_path = _resolve_viz_path(save_path)
    plt.figure(figsize=(10, 8))
    unique_labels = sorted(np.unique(labels))

    for idx, cluster_id in enumerate(unique_labels):
        mask = (labels == cluster_id)
        if not np.any(mask):
            continue
        plt.scatter(
            X_pca[mask, 0],
            X_pca[mask, 1],
            s=25,
            color=PALETTE[idx % len(PALETTE)],
            alpha=0.55,
            label=cluster_names.get(cluster_id, f"Cluster {cluster_id}"),
            edgecolors="none"
        )
        # Compute and plot centroid
        center_x = np.mean(X_pca[mask, 0])
        center_y = np.mean(X_pca[mask, 1])
        plt.scatter(center_x, center_y, s=180, color=PALETTE[idx % len(PALETTE)], edgecolors="black", linewidths=1.8, marker="X")

    plt.title("Principal Component Analysis (PCA) 2D Projection of Customer Segments", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel(f"Principal Component 1 ({explained_var[0]*100:.1f}% Variance Explained)", fontsize=11)
    plt.ylabel(f"Principal Component 2 ({explained_var[1]*100:.1f}% Variance Explained)", fontsize=11)
    plt.legend(title="Customer Persona", loc="upper right", frameon=True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved PCA projection to {save_path}")


def plot_tsne_scatter(
    X_tsne: np.ndarray,
    labels: np.ndarray,
    cluster_names: Dict[int, str],
    save_path: str = "visualizations/07_tsne_manifold_projection.png"
) -> None:
    """Plot t-SNE 2D manifold representation."""
    save_path = _resolve_viz_path(save_path)
    plt.figure(figsize=(10, 8))
    unique_labels = sorted(np.unique(labels))

    for idx, cluster_id in enumerate(unique_labels):
        mask = (labels == cluster_id)
        if not np.any(mask):
            continue
        plt.scatter(
            X_tsne[mask, 0],
            X_tsne[mask, 1],
            s=25,
            color=PALETTE[idx % len(PALETTE)],
            alpha=0.6,
            label=cluster_names.get(cluster_id, f"Cluster {cluster_id}"),
            edgecolors="none"
        )

    plt.title("t-SNE Non-Linear Manifold Projection of Customer Clusters", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("t-SNE Dimension 1", fontsize=11)
    plt.ylabel("t-SNE Dimension 2", fontsize=11)
    plt.legend(title="Customer Persona", loc="best", frameon=True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved t-SNE projection to {save_path}")


def plot_radar_profiles(
    scaled_df: pd.DataFrame,
    labels: np.ndarray,
    cluster_names: Dict[int, str],
    feature_cols: List[str],
    save_path: str = "visualizations/08_cluster_radar_profiles.png"
) -> None:
    """Plot radar/spider chart comparing standardized cluster centroids across features."""
    save_path = _resolve_viz_path(save_path)
    df_temp = scaled_df[feature_cols].copy()
    df_temp['Cluster'] = labels
    cluster_means = df_temp.groupby('Cluster').mean()

    num_vars = len(feature_cols)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Close the loop

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for i, (cluster_idx, row) in enumerate(cluster_means.iterrows()):
        values = row.values.flatten().tolist()
        values += values[:1]
        color = PALETTE[i % len(PALETTE)]
        name = cluster_names.get(cluster_idx, f"Cluster {cluster_idx}")

        ax.plot(angles, values, linewidth=2.0, color=color, label=name)
        ax.fill(angles, values, color=color, alpha=0.15)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), feature_cols, fontsize=10, fontweight="bold")
    ax.set_title("Customer Segment Behavioral Profiles (Standardized Centroid Radar)", fontsize=13, fontweight="bold", pad=25)
    plt.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), frameon=True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved radar profiles to {save_path}")


def plot_cluster_boxplots(
    df_cust: pd.DataFrame,
    cluster_names: Dict[int, str],
    save_path: str = "visualizations/09_cluster_boxplots_metrics.png"
) -> None:
    """Generate multi-panel boxplots of core unscaled metrics by customer cluster."""
    save_path = _resolve_viz_path(save_path)
    features = ['Recency', 'Frequency', 'Monetary', 'AvgBasketSize']
    ylabels = ['Recency (Days)', 'Order Count', 'Total Spend (£)', 'Items per Order']
    
    df_plot = df_cust.copy()
    df_plot['Persona'] = df_plot['Cluster'].map(cluster_names)
    persona_order = [cluster_names[i] for i in sorted(cluster_names.keys())]

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("Key Metric Distributions Across Customer Personas", fontsize=14, y=0.98)

    for i, (feat, ylab) in enumerate(zip(features, ylabels)):
        ax = axes[i // 2, i % 2]
        sns.boxplot(
            x='Persona',
            y=feat,
            hue='Persona',
            legend=False,
            data=df_plot,
            order=persona_order,
            palette=PALETTE,
            ax=ax,
            showfliers=False,  # Exclude extreme outliers for clean visualization of central 90%
            width=0.55
        )
        ax.set_title(f"{feat} by Segment (Excluding Outliers for Visual Clarity)", fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel(ylab)
        ax.tick_params(axis='x', rotation=15)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved cluster boxplots to {save_path}")


def plot_revenue_and_population_share(
    df_cust: pd.DataFrame,
    cluster_names: Dict[int, str],
    save_path: str = "visualizations/10_revenue_contribution_and_sizes.png"
) -> None:
    """Plot dual-bar comparison: Customer Population Share (%) vs Total Revenue Share (%)."""
    save_path = _resolve_viz_path(save_path)
    counts = df_cust['Cluster'].value_counts().sort_index()
    pop_pct = (counts / len(df_cust) * 100).values

    total_rev = df_cust['Monetary'].sum()
    rev_per_cluster = df_cust.groupby('Cluster')['Monetary'].sum().sort_index()
    rev_pct = (rev_per_cluster / total_rev * 100).values

    labels = [cluster_names.get(i, f"Cluster {i}") for i in sorted(cluster_names.keys())]

    x = np.arange(len(labels))
    width = 0.35

    plt.figure(figsize=(10, 6))
    bar1 = plt.bar(x - width/2, pop_pct, width, label='Customer Population Share (%)', color='#2E86AB', alpha=0.9)
    bar2 = plt.bar(x + width/2, rev_pct, width, label='Total Revenue Share (%)', color='#D9534F', alpha=0.9)

    # Add data labels
    for rect in bar1:
        h = rect.get_height()
        plt.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight="bold")

    for rect in bar2:
        h = rect.get_height()
        plt.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight="bold")

    plt.title("Economic Disparity: Customer Population Share vs. Revenue Contribution", fontsize=13, fontweight="bold", pad=12)
    plt.ylabel("Percentage of Total (%)")
    plt.xticks(x, labels, rotation=10, fontweight="bold")
    plt.ylim([0, max(max(pop_pct), max(rev_pct)) + 12])
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[VIZ] Saved revenue vs population share to {save_path}")
