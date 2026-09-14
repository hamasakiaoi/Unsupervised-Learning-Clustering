# Week 3 Internship Project: Unsupervised Learning & Customer Behavioral Clustering Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4%2B-orange.svg)](https://scikit-learn.org/)
[![Status: Complete](https://img.shields.io/badge/Internship%20Evaluation-Ready-green.svg)]()

An end-to-end unsupervised machine learning project modeling latent customer behavioral typologies from real-world e-commerce transaction logs. Developed as a standalone submission for the **Week 3 Internship Milestone: Unsupervised Learning and Clustering Analysis**.

---

## Executive Summary & Findings

This project implements a complete, mathematically defensible analytical chain to segment 4,334 customer accounts from 541,909 raw transactional event logs (UCI Online Retail Dataset). 

Distance-based clustering algorithms (such as K-Means and Ward's Hierarchical Clustering) are vulnerable to severe power-law skewness and scale imbalances common in commercial retail data. By combining customer-level behavioral feature engineering, variance-stabilizing logarithmic transformations ($y = \log(1 + x)$), and isotropic z-score scaling, the pipeline uncovers four highly stable, commercially distinct customer archetypes.

### Discovered Customer Personas ($k=4$)

| Cluster ID | Persona Archetype | Customer Count (%) | Revenue Share (%) | Median Recency | Median Frequency | Median Spend (£) | Median Basket Size |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cluster 1** | **Champions / Power Retailers** | 1,060 (24.46%) | **£6,644,441.65 (75.99%)** | 14.0 days | 7.0 orders | £2,979.97 | 259.9 items |
| **Cluster 3** | **Active Regular Customers** | 1,487 (34.31%) | £1,280,575.97 (14.65%) | 43.0 days | 3.0 orders | £752.44 | 135.7 items |
| **Cluster 2** | **At-Risk Bulk Buyers** | 951 (21.94%) | £679,939.76 (7.78%) | 106.0 days | 1.0 orders | £391.98 | 238.0 items |
| **Cluster 0** | **Low-Value / Churned Buyers** | 836 (19.29%) | £138,956.26 (1.59%) | 165.5 days | 1.0 orders | £152.13 | 65.0 items |

> **Key Empirical Discovery**: The customer base exhibits a classic manifestation of the **Pareto Principle (80/20 Rule)**: ~24.5% of accounts generate ~76.0% of all company sales. Targeted VIP retention for Cluster 1 and basket-expansion cross-selling for Cluster 3 represent the highest-ROI commercial opportunities.

---

## Repository Structure

```
Week_3/
├── data/
│   ├── raw/
│   │   ├── dataset_metadata.json          # Verified UCI repository metadata
│   │   └── online_retail.csv              # Cached raw transaction dataset (541,909 rows)
│   └── processed/
│       ├── customer_features.csv          # Engineered unscaled customer behavioral profiles
│       ├── scaled_features.csv            # Log-transformed and standardized clustering matrix
│       ├── cluster_profile_summary.csv    # Executive summary statistics per segment
│       ├── kmeans_evaluation_metrics.csv  # WCSS, Silhouette, CH, DB scores across k=2..7
│       └── pca_feature_loadings.csv       # PCA eigenvectors and variance ratios
├── notebooks/
│   └── clustering_analysis.ipynb          # 20-section analytical narrative Jupyter Notebook
├── src/
│   ├── __init__.py
│   ├── data_loading.py                    # Automated dataset retrieval and caching
│   ├── preprocessing.py                   # Data cleaning, RFM engineering, log1p, scaling
│   ├── clustering.py                      # K-Means, Ward Hierarchical, PCA, t-SNE
│   ├── evaluation.py                      # Internal validation metrics and bootstrap stability
│   └── visualization.py                   # Publication-quality plotting suite (300 DPI)
├── visualizations/
│   ├── 01_raw_vs_log_distributions.png    # Variance stabilization histogram comparison
│   ├── 02_feature_correlation_heatmap.png # Pearson correlation matrix
│   ├── 03_cluster_evaluation_metrics.png  # 4-panel evaluation grid (Elbow, Sil, CH, DB)
│   ├── 04_hierarchical_dendrogram.png     # Ward's minimum variance dendrogram (k=4 cut)
│   ├── 05_silhouette_analysis.png         # Silhouette coefficient widths by cluster
│   ├── 06_pca_2d_projection.png           # 2D PCA projection (79.6% cumulative variance)
│   ├── 07_tsne_manifold_projection.png    # 2D t-SNE non-linear manifold projection
│   ├── 08_cluster_radar_profiles.png      # Radar chart of standardized centroid z-scores
│   ├── 09_cluster_boxplots_metrics.png    # Metric distribution boxplots by persona
│   └── 10_revenue_contribution_and_sizes.png # Economic disparity bar chart
├── report/
│   └── Week_3_Clustering_Report.docx      # 24-section formal DOCX report with embedded figures
├── tests/
│   └── test_pipeline.py                   # Automated unit test verification suite
├── main_analysis.py                       # End-to-end execution pipeline driver
├── generate_report.py                     # Report compiler and formatting script
├── requirements.txt                       # Pinned runtime dependencies
├── .gitignore                             # Data science gitignore
├── LICENSE                                # MIT Open Source License
└── README.md                              # Complete project documentation
```

---

## Methodology & Analytical Chain

```
Raw E-Commerce Event Logs (541,909 Transactions)
          ↓
Data Quality Audit (Filter 135k anonymous guest checkouts, 5k duplicates, non-product fees)
          ↓
Customer Behavioral Feature Engineering (Recency, Frequency, Monetary, AOV, Basket Size, SKUs, Tenure)
          ↓
Distributional Transformation (Log1p transformation reducing skewness from +48.01 to -0.36)
          ↓
Standardization (StandardScaler achieving zero mean and unit variance for isotropic distance)
          ↓
Candidate Cluster Count Evaluation (Testing k=2..7 on Elbow WCSS, Silhouette, Calinski-Harabasz, Davies-Bouldin)
          ↓
Model Selection (K-Means++ k=4 corroborated by Ward's Hierarchical Dendrogram cut)
          ↓
Validation & Stability Testing (10-fold 80% bootstrap subsampling yielding Mean ARI = 0.9428)
          ↓
Dimensionality Reduction & Manifold Inspection (2D PCA explaining 79.6% variance and t-SNE)
          ↓
Multi-Dimensional Profiling (Parametric means, non-parametric medians, revenue contributions)
          ↓
Commercial Strategic Interventions (VIP retention, basket expansion, seasonal reactivation)
```

---

## Dataset Acquisition & Licensing

- **Name**: Online Retail Dataset
- **Repository**: [UCI Machine Learning Repository (Dataset ID: 352)](https://archive.ics.uci.edu/dataset/352/online+retail)
- **Direct Archive**: `https://archive.ics.uci.edu/static/public/352/online+retail.zip`
- **Citation**: Chen, D., Sain, S. L., & Guo, K. (2012). Data mining for the online retail industry: A case study of RFM model-based customer segmentation using data mining. *Journal of Database Marketing & Customer Strategy Management*, 19(3), 197–208.
- **Licensing**: Creative Commons Attribution 4.0 International (CC BY 4.0). Redistribution and commercial usage permitted with attribution.
- **Acquisition**: The script `src/data_loading.py` automatically downloads the official archive, extracts the Excel sheet in memory, verifies file integrity, and caches the dataset as `data/raw/online_retail.csv`.

---

## Installation & Environment Setup

### 1. Clone or Open Workspace
Ensure you are located within the project root directory:
```bash
cd /home/hamasaki/Documents/Internship/Week_3
```

### 2. Install Required Dependencies
Install the required packages using pip:
```bash
pip install -r requirements.txt
```

Verified library versions:
- Python 3.10+ (tested on Python 3.14)
- `scikit-learn` >= 1.4.0
- `pandas` >= 2.2.0
- `numpy` >= 1.26.0
- `scipy` >= 1.12.0
- `matplotlib` >= 3.8.0
- `seaborn` >= 0.13.0
- `python-docx` >= 1.1.0
- `openpyxl` >= 3.1.0

---

## Execution Instructions

### Run the Full Pipeline End-to-End
Execute the main driver script to perform data loading, preprocessing, model training, metric evaluation, statistical profiling, and figure generation:
```bash
python3 main_analysis.py
```

### Run Automated Unit Tests
Run the automated test suite verifying all pipeline components (data loading, cleaning, RFM engineering, log1p scaling, K-Means, Ward hierarchical clustering, PCA, bootstrap stability, and figure assets):
```bash
# Direct runner
python3 tests/test_pipeline.py

# Or via standard unittest runner
python3 -m unittest discover -s tests -p "test_*.py"

# Or via pytest (if installed)
pytest tests/
```

### Re-Generate the DOCX Report
To rebuild the submission document `report/Week_3_Clustering_Report.docx` with updated statistical tables and embedded figures:
```bash
python3 generate_report.py
```

### Interactive Jupyter Notebook
Launch Jupyter to explore the step-by-step narrative notebook:
```bash
jupyter notebook notebooks/clustering_analysis.ipynb
```

---

## Summary of Cluster Profiles

### 1. Champions / Power Retailers (Cluster 1)
- **Profile**: 1,060 accounts (24.46% of base) generating £6,644,441.65 (75.99% of total revenue).
- **Metrics**: Median Recency = 14 days, Median Orders = 7, Median Spend = £2,979.97, Median Basket = 260 items, Median SKUs = 111 products.
- **Strategy**: Dedicated B2B key account management, VIP wholesale tiered pricing, priority fulfillment, and proactive churn monitoring.

### 2. Active Regular Customers (Cluster 3)
- **Profile**: 1,487 accounts (34.31% of base) generating £1,280,575.97 (14.65% of total revenue).
- **Metrics**: Median Recency = 43 days, Median Orders = 3, Median Spend = £752.44, Median Basket = 136 items, Median SKUs = 41 products.
- **Strategy**: Product recommendation cross-selling, basket expansion thresholds (£250 free delivery), and scheduled replenishment cadences.

### 3. At-Risk Bulk Buyers (Cluster 2)
- **Profile**: 951 accounts (21.94% of base) generating £679,939.76 (7.78% of total revenue).
- **Metrics**: Median Recency = 106 days, Median Orders = 1, Median Spend = £391.98, Median Basket = 238 items, Median SKUs = 23 products.
- **Strategy**: High-touch seasonal win-back outreach, corporate gifting catalogs, and incentives for recurring scheduled reorders.

### 4. Low-Value / Churned Buyers (Cluster 0)
- **Profile**: 836 accounts (19.29% of base) generating £138,956.26 (1.59% of total revenue).
- **Metrics**: Median Recency = 165.5 days, Median Orders = 1, Median Spend = £152.13, Median Basket = 65 items, Median SKUs = 9 products.
- **Strategy**: Automated low-cost email clearance blasts with steep discount coupons; cease high-cost paid retargeting.

---

## Limitations & Disclaimers

1. **Non-Causal Inference**: Clustering groups customers based on statistical proximity in transformed feature space. It identifies behavioral associations, not causal drivers of purchase decisions.
2. **Exclusion of Demographic Variables**: All features reflect transactional log activity. No consumer age, gender, corporate revenue, or organizational hierarchy data was available.
3. **Temporal Truncation**: Customer histories are observed over a 12-month period (Dec 2010 to Dec 2011). Multi-year seasonal lifecycles cannot be completely uncoupled from organic relationship aging.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
