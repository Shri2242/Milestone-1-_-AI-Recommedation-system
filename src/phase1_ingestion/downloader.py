"""
Dataset Downloader
==================
Fetches the Zomato restaurant dataset from Hugging Face and saves it locally.

Handles edge cases:
- EC-1.1: Hugging Face API unavailable / rate limited
- EC-1.3: Empty dataset
- EC-1.7: Extremely large dataset
- EC-1.8: Disk space insufficient
"""

import os
import sys
import time
import shutil
import logging
from pathlib import Path

import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.phase0.config import DATASET_NAME, DATASET_CACHE_DIR, DATASET_MAX_ROWS, DATA_DIR

logger = logging.getLogger("data_ingestion.downloader")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RAW_DATA_FILE = DATA_DIR / "raw_zomato.csv"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5  # exponential backoff base
MIN_DISK_SPACE_MB = 100


def check_disk_space(path: Path, required_mb: int = MIN_DISK_SPACE_MB) -> bool:
    """
    Check if there is sufficient disk space (EC-1.8).

    Args:
        path: Directory to check
        required_mb: Minimum required space in MB

    Returns:
        True if enough space is available
    """
    try:
        total, used, free = shutil.disk_usage(path.anchor)
        free_mb = free / (1024 * 1024)
        if free_mb < required_mb:
            logger.error(
                f"Insufficient disk space. Available: {free_mb:.0f} MB, "
                f"Required: {required_mb} MB."
            )
            return False
        logger.info(f"Disk space check passed: {free_mb:.0f} MB available.")
        return True
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")
        return True  # proceed cautiously


def download_dataset() -> pd.DataFrame:
    """
    Download the Zomato dataset from Hugging Face with retry logic (EC-1.1).

    Returns:
        Raw dataset as a pandas DataFrame

    Raises:
        RuntimeError: If download fails after all retries
    """
    # Check if we already have a cached copy
    if RAW_DATA_FILE.exists():
        logger.info(f"Found cached dataset at {RAW_DATA_FILE}. Loading from cache...")
        try:
            df = pd.read_csv(RAW_DATA_FILE)
            if len(df) > 0:
                logger.info(f"Loaded {len(df)} rows from cache.")
                return df
            else:
                logger.warning("Cached file is empty. Re-downloading...")
        except Exception as e:
            logger.warning(f"Failed to read cached file: {e}. Re-downloading...")

    # Check disk space (EC-1.8)
    if not check_disk_space(DATA_DIR):
        raise RuntimeError(
            f"Insufficient disk space. Need at least {MIN_DISK_SPACE_MB} MB free."
        )

    # Attempt download with retries (EC-1.1)
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"Downloading dataset '{DATASET_NAME}' from Hugging Face "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )

            from datasets import load_dataset

            dataset = load_dataset(DATASET_NAME, split="train")

            # Convert to DataFrame
            df = dataset.to_pandas()

            # Enforce row limit (EC-1.7)
            if len(df) > DATASET_MAX_ROWS:
                logger.warning(
                    f"Dataset has {len(df)} rows, exceeding limit of {DATASET_MAX_ROWS}. "
                    f"Truncating..."
                )
                df = df.head(DATASET_MAX_ROWS)

            # Check for empty dataset (EC-1.3)
            if len(df) == 0:
                raise ValueError("Dataset appears to be empty (0 rows).")

            # Save raw data to cache
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            df.to_csv(RAW_DATA_FILE, index=False)
            logger.info(
                f"Dataset downloaded successfully: {len(df)} rows, "
                f"{len(df.columns)} columns."
            )
            logger.info(f"Saved raw data to {RAW_DATA_FILE}")

            return df

        except Exception as e:
            last_error = e
            logger.error(f"Download attempt {attempt} failed: {e}")

            if attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    # All retries exhausted
    # Check for local cached copy as final fallback
    if RAW_DATA_FILE.exists():
        logger.warning(
            "All download attempts failed. Falling back to cached copy..."
        )
        return pd.read_csv(RAW_DATA_FILE)

    raise RuntimeError(
        f"Failed to download dataset after {MAX_RETRIES} attempts. "
        f"Last error: {last_error}\n"
        f"Please check your internet connection and try again."
    )


def get_raw_data() -> pd.DataFrame:
    """
    Get the raw dataset, downloading if necessary.

    Returns:
        Raw Zomato dataset as DataFrame
    """
    return download_dataset()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    logger.info("Starting dataset download...")
    df = download_dataset()
    logger.info(f"Done! Shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    print(df.head())
