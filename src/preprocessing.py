"""
Data Preprocessing, Cleaning, and Feature Engineering Module.

Transforms transaction-level retail records into a customer-level
behavioral feature matrix with rigorous handling of cancellations,
skewness, and scaling.
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.preprocessing import StandardScaler, RobustScaler

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def clean_transactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean transaction records:
    1. Deduplicate records.
    2. Filter records missing CustomerID (documented as anonymous guest sessions).
    3. Separate valid consumer purchases from cancellations / credit notes.
    4. Remove administrative non-product transactions and invalid unit prices.

    Returns:
        purchases (pd.DataFrame): Valid purchase transactions.
        cancellations (pd.DataFrame): Cancelled / return transactions.
    """
    print(f"[PREPROC] Initial transaction count: {len(df):,}")
    df_clean = df.drop_duplicates().copy()
    print(f"[PREPROC] After removing duplicates: {len(df_clean):,}")

    # Identify missing customer records
    missing_cust = df_clean['CustomerID'].isnull().sum()
    print(f"[PREPROC] Anonymous transactions without CustomerID: {missing_cust:,} ({missing_cust/len(df_clean)*100:.2f}%)")
    df_clean = df_clean.dropna(subset=['CustomerID']).copy()
    df_clean['CustomerID'] = pd.to_numeric(df_clean['CustomerID'], errors='coerce').astype(int).astype(str)

    # Filter non-product codes (postage, bank charges, Amazon fee, manual adjustments)
    admin_codes = {'POST', 'D', 'DOT', 'M', 'BANK CHARGES', 'AMAZONFEE', 'CRATE', 'S'}
    df_clean = df_clean[~df_clean['StockCode'].isin(admin_codes)].copy()

    # Cancellations are marked with 'C' in InvoiceNo or negative quantity
    is_cancelled = df_clean['InvoiceNo'].str.startswith('C', na=False) | (df_clean['Quantity'] <= 0)
    cancellations = df_clean[is_cancelled].copy()
    
    # Valid purchases must have positive Quantity and positive UnitPrice
    purchases = df_clean[(~is_cancelled) & (df_clean['Quantity'] > 0) & (df_clean['UnitPrice'] > 0)].copy()
    purchases['LineTotal'] = purchases['Quantity'] * purchases['UnitPrice']

    print(f"[PREPROC] Valid customer purchases: {len(purchases):,} records across {purchases['CustomerID'].nunique():,} customers.")
    print(f"[PREPROC] Recorded cancellations: {len(cancellations):,} records.")
    return purchases, cancellations


def engineer_customer_features(
    purchases: pd.DataFrame,
    cancellations: pd.DataFrame,
    snapshot_date: Optional[pd.Timestamp] = None
) -> pd.DataFrame:
    """
    Aggregate transaction data into a rich customer behavioral profile:
    - Recency: Days since last transaction relative to snapshot date.
    - Frequency: Count of distinct purchase invoices.
    - Monetary: Total net spend across purchases.
    - TotalUnits: Total physical item quantity purchased.
    - UniqueSKUs: Number of distinct product codes purchased.
    - AvgUnitPrice: Average unit price of items purchased.
    - Tenure: Days between customer's first and last transaction.
    - AOV: Average Order Value (Monetary / Frequency).
    - AvgBasketSize: Average items per order (TotalUnits / Frequency).
    - CancelledOrders: Distinct cancelled invoice count.
    - CancellationRate: Cancelled orders / (Frequency + Cancelled orders).
    """
    if snapshot_date is None:
        snapshot_date = purchases['InvoiceDate'].max() + pd.Timedelta(days=1)
    print(f"[PREPROC] Computing customer metrics relative to snapshot: {snapshot_date.strftime('%Y-%m-%d %H:%M')}")

    cust_agg = purchases.groupby('CustomerID').agg(
        Recency=('InvoiceDate', lambda dates: (snapshot_date - dates.max()).days),
        Frequency=('InvoiceNo', 'nunique'),
        Monetary=('LineTotal', 'sum'),
        TotalUnits=('Quantity', 'sum'),
        UniqueSKUs=('StockCode', 'nunique'),
        AvgUnitPrice=('UnitPrice', 'mean'),
        FirstPurchase=('InvoiceDate', 'min'),
        LastPurchase=('InvoiceDate', 'max')
    ).reset_index()

    cust_agg['Tenure'] = (cust_agg['LastPurchase'] - cust_agg['FirstPurchase']).dt.days
    cust_agg['AOV'] = cust_agg['Monetary'] / cust_agg['Frequency']
    cust_agg['AvgBasketSize'] = cust_agg['TotalUnits'] / cust_agg['Frequency']

    # Attach cancellation metrics
    canc_agg = cancellations.groupby('CustomerID')['InvoiceNo'].nunique().rename('CancelledOrders')
    cust_agg = cust_agg.merge(canc_agg, on='CustomerID', how='left')
    cust_agg['CancelledOrders'] = cust_agg['CancelledOrders'].fillna(0).astype(int)
    cust_agg['CancellationRate'] = cust_agg['CancelledOrders'] / (cust_agg['Frequency'] + cust_agg['CancelledOrders'])

    cust_agg.drop(columns=['FirstPurchase', 'LastPurchase'], inplace=True)
    print(f"[PREPROC] Successfully engineered {len(cust_agg):,} customer profiles across {cust_agg.shape[1]} metrics.")
    return cust_agg


# Recommended clustering feature set
CORE_FEATURES = [
    'Recency', 'Frequency', 'Monetary',
    'AOV', 'AvgBasketSize', 'UniqueSKUs', 'Tenure'
]


def prepare_clustering_matrix(
    df_cust: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    scale_method: str = "standard"
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, object]:
    """
    Prepares the clustering feature matrix:
    1. Selects core numerical features.
    2. Applies log1p transformation to eliminate positive skewness.
    3. Scales features to mean=0, std=1 (or robust median/IQR).

    Returns:
        X_raw (pd.DataFrame): Original unscaled features.
        X_log (pd.DataFrame): Log1p-transformed features.
        X_scaled (np.ndarray): Scaled numerical matrix ready for clustering.
        scaler (object): Fitted scaler instance.
    """
    if feature_cols is None:
        feature_cols = CORE_FEATURES

    X_raw = df_cust[feature_cols].copy()
    
    # Verify non-negative values for log1p
    for col in feature_cols:
        if (X_raw[col] < 0).any():
            min_val = X_raw[col].min()
            X_raw[col] = X_raw[col] - min_val

    # Convert to pure float64 numpy array for robust numerical stability
    X_raw_vals = X_raw.to_numpy(dtype=np.float64)
    X_log_vals = np.log1p(X_raw_vals)
    
    X_log = pd.DataFrame(
        X_log_vals,
        columns=[f"{col}_log" for col in feature_cols],
        index=X_raw.index
    )

    if scale_method == "standard":
        scaler = StandardScaler()
    elif scale_method == "robust":
        scaler = RobustScaler()
    else:
        raise ValueError(f"Unknown scaling method '{scale_method}'. Choose 'standard' or 'robust'.")

    X_scaled = scaler.fit_transform(X_log_vals)
    print(f"[PREPROC] Scaled feature matrix: shape {X_scaled.shape}, mean={X_scaled.mean():.4e}, std={X_scaled.std():.4f}")
    return X_raw, X_log, X_scaled, scaler


def save_processed_data(
    df_cust: pd.DataFrame,
    X_scaled: np.ndarray,
    feature_names: List[str],
    out_dir: str = "data/processed"
) -> None:
    """Save processed customer data and scaled matrix to disk."""
    if not os.path.isabs(out_dir):
        from src.data_loading import get_project_root
        out_dir = os.path.join(get_project_root(), out_dir)

    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "customer_features.csv")
    df_cust.to_csv(csv_path, index=False)
    
    scaled_df = pd.DataFrame(X_scaled, columns=feature_names)
    scaled_df['CustomerID'] = df_cust['CustomerID'].values
    scaled_path = os.path.join(out_dir, "scaled_features.csv")
    scaled_df.to_csv(scaled_path, index=False)
    print(f"[PREPROC] Processed customer features saved to {csv_path} and {scaled_path}")


if __name__ == "__main__":
    from src.data_loading import load_raw_data
    df_raw = load_raw_data()
    purchases, cancellations = clean_transactions(df_raw)
    df_cust = engineer_customer_features(purchases, cancellations)
    X_raw, X_log, X_scaled, scaler = prepare_clustering_matrix(df_cust)
    save_processed_data(df_cust, X_scaled, CORE_FEATURES)
