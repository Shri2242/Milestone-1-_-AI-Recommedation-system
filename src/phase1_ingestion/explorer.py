"""
Dataset Explorer
================
Generates summary statistics and insights from the processed Zomato dataset.
Useful for validation, debugging, and understanding the data distribution.
"""

import sys
import logging
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("data_ingestion.explorer")


def explore(df: pd.DataFrame) -> dict:
    """
    Generate comprehensive summary statistics for the dataset.

    Args:
        df: Processed DataFrame

    Returns:
        Dictionary of summary statistics
    """
    stats = {}

    # Basic shape
    stats["total_rows"] = len(df)
    stats["total_columns"] = len(df.columns)
    stats["columns"] = list(df.columns)

    # --- City / Location distribution ---
    if "city" in df.columns:
        city_counts = df["city"].value_counts()
        stats["unique_cities"] = len(city_counts)
        stats["top_10_cities"] = city_counts.head(10).to_dict()

    # --- Cuisine distribution ---
    if "cuisines" in df.columns:
        # Each row can have multiple cuisines separated by commas
        all_cuisines = (
            df["cuisines"]
            .str.split(",")
            .explode()
            .str.strip()
            .value_counts()
        )
        stats["unique_cuisines"] = len(all_cuisines)
        stats["top_15_cuisines"] = all_cuisines.head(15).to_dict()

    # --- Rating distribution ---
    if "rating" in df.columns:
        stats["rating_stats"] = {
            "mean": round(df["rating"].mean(), 2),
            "median": round(df["rating"].median(), 2),
            "min": round(df["rating"].min(), 2),
            "max": round(df["rating"].max(), 2),
            "std": round(df["rating"].std(), 2),
        }
        # Rating buckets
        stats["rating_distribution"] = {
            "0 (Unrated)": int((df["rating"] == 0).sum()),
            "0.1 - 2.0 (Poor)": int(((df["rating"] > 0) & (df["rating"] <= 2.0)).sum()),
            "2.1 - 3.0 (Average)": int(((df["rating"] > 2.0) & (df["rating"] <= 3.0)).sum()),
            "3.1 - 4.0 (Good)": int(((df["rating"] > 3.0) & (df["rating"] <= 4.0)).sum()),
            "4.1 - 5.0 (Excellent)": int(((df["rating"] > 4.0) & (df["rating"] <= 5.0)).sum()),
        }

    # --- Cost distribution ---
    if "cost_for_two" in df.columns:
        stats["cost_stats"] = {
            "mean": round(df["cost_for_two"].mean(), 2),
            "median": round(df["cost_for_two"].median(), 2),
            "min": int(df["cost_for_two"].min()),
            "max": int(df["cost_for_two"].max()),
        }
        # Budget buckets (matching Phase 2 budget mapping)
        stats["budget_distribution"] = {
            "Low (0–500)": int((df["cost_for_two"] <= 500).sum()),
            "Medium (500–1500)": int(((df["cost_for_two"] > 500) & (df["cost_for_two"] <= 1500)).sum()),
            "High (1500+)": int((df["cost_for_two"] > 1500).sum()),
        }

    # --- Votes ---
    if "votes" in df.columns:
        stats["votes_stats"] = {
            "mean": round(df["votes"].mean(), 2),
            "median": round(df["votes"].median(), 2),
            "max": int(df["votes"].max()),
            "total": int(df["votes"].sum()),
        }

    # --- Boolean features ---
    for col in ["has_online_delivery", "has_table_booking"]:
        if col in df.columns:
            stats[col] = {
                "True": int(df[col].sum()),
                "False": int((~df[col]).sum()),
            }

    # --- Missing values summary ---
    missing = df.isna().sum()
    missing_cols = missing[missing > 0].to_dict()
    stats["missing_values"] = missing_cols if missing_cols else "None"

    return stats


def print_report(stats: dict):
    """
    Print a formatted summary report to the console.

    Args:
        stats: Dictionary from explore()
    """
    separator = "=" * 60

    print(f"\n{separator}")
    print("[REPORT] DATASET EXPLORATION REPORT")
    print(separator)

    print(f"\n[SHAPE] {stats['total_rows']} rows x {stats['total_columns']} columns")
    print(f"[COLUMNS] {', '.join(stats['columns'])}")

    if "unique_cities" in stats:
        print(f"\n[CITIES] {stats['unique_cities']} unique")
        print("   Top 10:")
        for city, count in stats["top_10_cities"].items():
            bar = "#" * max(1, int(count / max(stats["top_10_cities"].values()) * 20))
            print(f"   {city:20s} {count:>5d}  {bar}")

    if "unique_cuisines" in stats:
        print(f"\n[CUISINES] {stats['unique_cuisines']} unique")
        print("   Top 15:")
        for cuisine, count in stats["top_15_cuisines"].items():
            bar = "#" * max(1, int(count / max(stats["top_15_cuisines"].values()) * 20))
            print(f"   {cuisine:25s} {count:>5d}  {bar}")

    if "rating_stats" in stats:
        r = stats["rating_stats"]
        print(f"\n[RATINGS] mean={r['mean']}, median={r['median']}, "
              f"range=[{r['min']}-{r['max']}], std={r['std']}")
        print("   Distribution:")
        for bucket, count in stats["rating_distribution"].items():
            bar = "#" * max(1, int(count / max(stats["rating_distribution"].values()) * 20))
            print(f"   {bucket:25s} {count:>5d}  {bar}")

    if "cost_stats" in stats:
        c = stats["cost_stats"]
        print(f"\n[COST] Cost for Two: mean={c['mean']}, median={c['median']}, "
              f"range=[{c['min']}-{c['max']}]")
        print("   Budget Distribution:")
        for bucket, count in stats["budget_distribution"].items():
            bar = "#" * max(1, int(count / max(stats["budget_distribution"].values()) * 20))
            print(f"   {bucket:25s} {count:>5d}  {bar}")

    if "votes_stats" in stats:
        v = stats["votes_stats"]
        print(f"\n[VOTES] mean={v['mean']}, median={v['median']}, "
              f"max={v['max']}, total={v['total']}")

    for col_label, col_key in [("[ONLINE DELIVERY]", "has_online_delivery"),
                                ("[TABLE BOOKING]", "has_table_booking")]:
        if col_key in stats:
            print(f"\n{col_label}: Yes={stats[col_key]['True']}, No={stats[col_key]['False']}")

    print(f"\n[MISSING] Missing Values: {stats['missing_values']}")
    print(f"\n{separator}\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    from src.phase1_ingestion.preprocessor import load_processed_data

    logger.info("Loading processed data for exploration...")
    df = load_processed_data()
    stats = explore(df)
    print_report(stats)
