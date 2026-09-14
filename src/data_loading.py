"""
Data Acquisition and Loading Module for UCI Online Retail Dataset.

This module handles automated dataset retrieval, extraction, caching,
and loading with robust error handling and path resolution.
"""

import os
import json
import io
import time
import zipfile
import urllib.request
import pandas as pd
from typing import Tuple, Optional

DATA_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
METADATA = {
    "dataset_name": "Online Retail",
    "source": "UCI Machine Learning Repository",
    "uci_id": 352,
    "source_url": "https://archive.ics.uci.edu/dataset/352/online+retail",
    "download_url": DATA_URL,
    "creators": ["Daqing Chen", "Sai Liang Sain", "Kun Guo"],
    "publication_year": 2012,
    "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
    "description": "Transnational transactional data containing all purchases for a UK-based online retail firm between 01/12/2010 and 09/12/2011.",
    "domain": "E-Commerce / Retail Customer Segmentation",
    "raw_row_count": 541909,
    "attributes": [
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country"
    ]
}


def get_project_root() -> str:
    """Return the absolute path to the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_data_paths(base_dir: Optional[str] = None) -> Tuple[str, str, str]:
    """Resolve data directory and file paths relative to project root."""
    if base_dir is not None:
        resolved_base = os.path.abspath(base_dir)
        # If specified base_dir doesn't contain the raw data but project root does, use project root
        if not os.path.exists(os.path.join(resolved_base, "data", "raw", "online_retail.csv")):
            proj_root = get_project_root()
            if os.path.exists(os.path.join(proj_root, "data", "raw", "online_retail.csv")):
                resolved_base = proj_root
    else:
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "data", "raw", "online_retail.csv")):
            resolved_base = cwd
        else:
            resolved_base = get_project_root()

    raw_dir = os.path.join(resolved_base, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    csv_path = os.path.join(raw_dir, "online_retail.csv")
    meta_path = os.path.join(raw_dir, "dataset_metadata.json")
    return raw_dir, csv_path, meta_path


def download_and_cache_dataset(raw_dir: str, csv_path: str, meta_path: str) -> None:
    """Download zip from UCI ML Repository, convert to CSV, and save metadata."""
    print(f"[INFO] Fetching dataset from {DATA_URL} ...")
    start_time = time.time()
    
    req = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req) as response:
        zip_bytes = response.read()
        
    download_elapsed = time.time() - start_time
    print(f"[INFO] Download completed in {download_elapsed:.2f}s ({len(zip_bytes) / (1024*1024):.1f} MB).")

    # Extract Excel from zip in-memory
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        excel_filename = None
        for name in zf.namelist():
            if name.endswith(".xlsx"):
                excel_filename = name
                break
        if not excel_filename:
            raise FileNotFoundError("No .xlsx file found in the downloaded archive.")

        print(f"[INFO] Extracting and parsing '{excel_filename}' ...")
        t0 = time.time()
        with zf.open(excel_filename) as excel_file:
            df = pd.read_excel(excel_file)
        print(f"[INFO] Excel parsed in {time.time() - t0:.2f}s. Shape: {df.shape}")

    # Cache as CSV for fast subsequent access
    print(f"[INFO] Caching parsed dataset to {csv_path} ...")
    df.to_csv(csv_path, index=False)

    # Save metadata
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(METADATA, f, indent=2)
    print(f"[INFO] Metadata saved to {meta_path}.")


def load_raw_data(base_dir: Optional[str] = None, force_download: bool = False) -> pd.DataFrame:
    """
    Load raw Online Retail transaction records into a pandas DataFrame.
    Automatically downloads and caches on first run.
    """
    raw_dir, csv_path, meta_path = get_data_paths(base_dir)

    if force_download or not os.path.exists(csv_path):
        download_and_cache_dataset(raw_dir, csv_path, meta_path)

    print(f"[INFO] Loading raw transactions from {csv_path} ...")
    t0 = time.time()
    df = pd.read_csv(
        csv_path,
        dtype={
            "InvoiceNo": str,
            "StockCode": str,
            "Description": str,
            "Quantity": "int64",
            "UnitPrice": "float64",
            "CustomerID": "float64",
            "Country": str
        },
        parse_dates=["InvoiceDate"]
    )
    print(f"[INFO] Successfully loaded {len(df):,} transactions in {time.time() - t0:.2f}s.")
    return df


if __name__ == "__main__":
    df_raw = load_raw_data()
    print("Columns:", df_raw.columns.tolist())
    print("Sample rows:\n", df_raw.head(3))
