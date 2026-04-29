"""
Dataset Preprocessor
====================
Cleans, normalizes, and transforms the raw Zomato dataset into a
structured format ready for filtering and recommendation.

Handles edge cases:
- EC-1.2: Dataset schema change
- EC-1.4: Missing values in critical fields
- EC-1.5: Duplicate restaurants
- EC-1.6: Corrupt or malformed data
"""

import sys
import logging
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.phase0.config import DATA_DIR

logger = logging.getLogger("data_ingestion.preprocessor")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROCESSED_DATA_FILE = DATA_DIR / "processed_zomato.csv"

# Expected columns (used for schema validation — EC-1.2)
# We define a flexible mapping: raw name → normalized name
COLUMN_MAPPING = {
    # Common variations we might encounter
    "name": "name",
    "restaurant name": "name",
    # Location / city mappings
    "city": "city",
    "location": "city",
    "listed_in(city)": "city",
    # Cuisine
    "cuisines": "cuisines",
    "cuisine": "cuisines",
    # Cost mappings — actual dataset uses 'approx_cost(for two people)'
    "approx_cost(for two people)": "cost_for_two",
    "average_cost_for_two": "cost_for_two",
    "cost_for_two": "cost_for_two",
    "average cost for two": "cost_for_two",
    # Rating — actual dataset uses 'rate'
    "rate": "rating",
    "aggregate_rating": "rating",
    "rating": "rating",
    "aggregate rating": "rating",
    # Votes
    "votes": "votes",
    # Boolean features — actual dataset uses 'online_order' and 'book_table'
    "online_order": "has_online_delivery",
    "has_online_delivery": "has_online_delivery",
    "has online delivery": "has_online_delivery",
    "book_table": "has_table_booking",
    "has_table_booking": "has_table_booking",
    "has table booking": "has_table_booking",
    # Other
    "currency": "currency",
    "country_code": "country_code",
    "country code": "country_code",
    "rest_type": "rest_type",
    "dish_liked": "dish_liked",
    "address": "address",
}

REQUIRED_COLUMNS = ["name", "city", "cuisines", "cost_for_two", "rating"]


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and normalize column names (EC-1.2).

    Attempts to map raw column names to expected normalized names.
    Raises a clear error if required columns are missing.

    Args:
        df: Raw DataFrame

    Returns:
        DataFrame with normalized column names
    """
    # Lowercase all column names for matching
    df.columns = [col.strip().lower().replace("  ", " ") for col in df.columns]

    # Map columns — handle duplicates by preferring the first mapped column
    rename_map = {}
    used_targets = set()
    for raw_col in df.columns:
        if raw_col in COLUMN_MAPPING:
            target = COLUMN_MAPPING[raw_col]
            if target not in used_targets:
                rename_map[raw_col] = target
                used_targets.add(target)

    df = df.rename(columns=rename_map)

    # Drop any remaining duplicate columns (keep first)
    df = df.loc[:, ~df.columns.duplicated()]

    # Check for required columns
    found_columns = set(df.columns)
    missing = [col for col in REQUIRED_COLUMNS if col not in found_columns]

    if missing:
        logger.error(
            f"Dataset schema validation failed!\n"
            f"  Missing columns: {missing}\n"
            f"  Found columns: {sorted(found_columns)}\n"
            f"  Expected: {REQUIRED_COLUMNS}"
        )
        raise ValueError(
            f"Dataset schema has changed. "
            f"Expected columns: {REQUIRED_COLUMNS}. "
            f"Missing: {missing}. "
            f"Found: {sorted(found_columns)}."
        )

    logger.info(f"Schema validation passed. Columns: {sorted(found_columns)}")
    return df


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in the dataset (EC-1.4).

    Strategy:
    - Drop rows where 'name' is null (restaurant must have a name)
    - Fill 'rating' nulls with 0.0 and flag as 'Unrated'
    - Fill 'cuisines' nulls with 'Unknown'
    - Fill 'city' nulls with 'Unknown'
    - Fill 'cost_for_two' nulls with 0

    Args:
        df: DataFrame with potential missing values

    Returns:
        Cleaned DataFrame
    """
    initial_rows = len(df)

    # Drop rows with no restaurant name
    name_nulls = df["name"].isna().sum()
    if name_nulls > 0:
        logger.info(f"Dropping {name_nulls} rows with missing restaurant name.")
        df = df.dropna(subset=["name"])

    # Fill missing ratings
    rating_nulls = df["rating"].isna().sum()
    if rating_nulls > 0:
        logger.info(f"Filling {rating_nulls} missing ratings with 0.0 (Unrated).")
        df["rating"] = df["rating"].fillna(0.0)

    # Fill missing cuisines
    cuisine_nulls = df["cuisines"].isna().sum()
    if cuisine_nulls > 0:
        logger.info(f"Filling {cuisine_nulls} missing cuisines with 'Unknown'.")
        df["cuisines"] = df["cuisines"].fillna("Unknown")

    # Fill missing city
    if "city" in df.columns:
        city_nulls = df["city"].isna().sum()
        if city_nulls > 0:
            logger.info(f"Filling {city_nulls} missing cities with 'Unknown'.")
            df["city"] = df["city"].fillna("Unknown")

    # Fill missing cost
    cost_nulls = df["cost_for_two"].isna().sum()
    if cost_nulls > 0:
        logger.info(f"Filling {cost_nulls} missing cost values with 0.")
        df["cost_for_two"] = df["cost_for_two"].fillna(0)

    final_rows = len(df)
    logger.info(
        f"Missing value cleanup: {initial_rows} → {final_rows} rows "
        f"({initial_rows - final_rows} removed)."
    )
    return df


def fix_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce columns to correct data types (EC-1.6).

    - rating → float
    - cost_for_two → int
    - votes → int
    - name, city, cuisines → stripped strings

    Args:
        df: DataFrame with potentially malformed types

    Returns:
        DataFrame with correct types
    """
    # Rating — actual dataset has values like "4.1/5", "NEW", "-"
    if df["rating"].dtype == object:
        # Strip "/5" suffix, handle "NEW" and "-" as 0
        df["rating"] = (
            df["rating"]
            .astype(str)
            .str.replace("/5", "", regex=False)
            .str.strip()
            .replace({"NEW": "0", "-": "0", "nan": "0", "": "0"})
        )
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)

    # Cost — actual dataset may have commas (e.g., "1,200")
    if df["cost_for_two"].dtype == object:
        df["cost_for_two"] = (
            df["cost_for_two"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
            .replace({"nan": "0", "": "0"})
        )
    df["cost_for_two"] = pd.to_numeric(df["cost_for_two"], errors="coerce").fillna(0).astype(int)

    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

    # String columns — strip whitespace
    for col in ["name", "city", "cuisines"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Normalize city to title case for consistent filtering
    if "city" in df.columns:
        df["city"] = df["city"].str.title()

    # Boolean columns
    for bool_col in ["has_online_delivery", "has_table_booking"]:
        if bool_col in df.columns:
            df[bool_col] = df[bool_col].map(
                {"Yes": True, "No": False, 1: True, 0: False, "1": True, "0": False}
            ).fillna(False).astype(bool)

    logger.info("Data types fixed and normalized.")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate restaurants (EC-1.5).

    Strategy: Keep the entry with the highest vote count when
    same name + same city appears multiple times.

    Args:
        df: DataFrame with potential duplicates

    Returns:
        Deduplicated DataFrame
    """
    initial_rows = len(df)

    if "votes" in df.columns:
        # Sort by votes descending, then drop duplicates keeping first (highest votes)
        df = df.sort_values("votes", ascending=False)
        df = df.drop_duplicates(subset=["name", "city"], keep="first")
    else:
        df = df.drop_duplicates(subset=["name", "city"], keep="first")

    duplicates_removed = initial_rows - len(df)
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate restaurants.")
    else:
        logger.info("No duplicates found.")

    return df.reset_index(drop=True)


def clamp_ratings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure ratings are within the valid 0.0–5.0 range.

    Args:
        df: DataFrame

    Returns:
        DataFrame with clamped ratings
    """
    out_of_range = ((df["rating"] < 0) | (df["rating"] > 5)).sum()
    if out_of_range > 0:
        logger.info(f"Clamping {out_of_range} ratings to 0.0–5.0 range.")
        df["rating"] = df["rating"].clip(0.0, 5.0)
    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline on raw data.

    Pipeline:
    1. Validate schema
    2. Fix data types
    3. Clean missing values
    4. Clamp ratings
    5. Remove duplicates

    Args:
        df: Raw DataFrame from downloader

    Returns:
        Cleaned, normalized DataFrame ready for filtering
    """
    logger.info(f"Starting preprocessing pipeline ({len(df)} rows)...")

    df = validate_schema(df)
    df = fix_data_types(df)
    df = clean_missing_values(df)
    df = clamp_ratings(df)
    df = remove_duplicates(df)

    # Select and order final columns
    final_columns = [
        col for col in [
            "name", "city", "cuisines", "cost_for_two", "rating",
            "votes", "has_online_delivery", "has_table_booking",
            "currency", "country_code",
        ]
        if col in df.columns
    ]
    df = df[final_columns]

    logger.info(f"Preprocessing complete: {len(df)} rows, {len(df.columns)} columns.")
    return df


def save_processed_data(df: pd.DataFrame) -> Path:
    """
    Save the processed dataset to CSV.

    Args:
        df: Processed DataFrame

    Returns:
        Path to the saved file
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DATA_FILE, index=False)
    size_mb = PROCESSED_DATA_FILE.stat().st_size / (1024 * 1024)
    logger.info(f"Saved processed data to {PROCESSED_DATA_FILE} ({size_mb:.2f} MB)")
    return PROCESSED_DATA_FILE


def load_processed_data() -> pd.DataFrame:
    """
    Load the processed dataset from disk.

    Returns:
        Processed DataFrame

    Raises:
        FileNotFoundError: If processed data doesn't exist yet
    """
    if not PROCESSED_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Processed data not found at {PROCESSED_DATA_FILE}. "
            f"Run the data ingestion pipeline first."
        )
    df = pd.read_csv(PROCESSED_DATA_FILE)
    logger.info(f"Loaded processed data: {len(df)} rows.")
    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    from src.phase1_ingestion.downloader import get_raw_data

    logger.info("Running preprocessing pipeline...")
    raw_df = get_raw_data()
    processed_df = preprocess(raw_df)
    save_processed_data(processed_df)
    print(f"\nProcessed dataset shape: {processed_df.shape}")
    print(f"\nSample rows:")
    print(processed_df.head(5).to_string())
