"""
Filter Engine
=============
Core multi-criteria restaurant filtering logic.

Applies filters in sequence: Location → Budget → Cuisine → Rating → Additional.
Supports progressive filter relaxation when no results are found (EC-2.1).

Handles edge cases:
- EC-2.1: No restaurants match all criteria (progressive relaxation)
- EC-2.5: Multiple cuisines selected
- EC-2.7: Minimum rating of 5.0
- EC-2.8: All fields left empty
- EC-2.10: Very large number of filtered results (cap at top N)
"""

import sys
import logging
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.phase0.config import MAX_FILTERED_RESULTS
from src.phase2_filtering.budget_mapper import get_cost_range, get_budget_label
from src.phase2_filtering.fuzzy_match import (
    fuzzy_match_single,
    fuzzy_match_multi,
    get_available_values,
)
from src.phase1_ingestion.preprocessor import load_processed_data

logger = logging.getLogger("filtering.filter_engine")


class FilterResult:
    """Encapsulates the result of a filtering operation."""

    def __init__(
        self,
        restaurants: pd.DataFrame,
        total_matches: int,
        filters_applied: dict,
        relaxed_filters: list[str],
        messages: list[str],
    ):
        self.restaurants = restaurants
        self.total_matches = total_matches
        self.filters_applied = filters_applied
        self.relaxed_filters = relaxed_filters
        self.messages = messages

    @property
    def has_results(self) -> bool:
        return len(self.restaurants) > 0

    @property
    def was_relaxed(self) -> bool:
        return len(self.relaxed_filters) > 0

    def to_dict_list(self) -> list[dict]:
        """Convert results to a list of dicts for template rendering or LLM prompt."""
        return self.restaurants.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Individual Filters
# ---------------------------------------------------------------------------


def _filter_by_location(df: pd.DataFrame, location: str) -> tuple[pd.DataFrame, list[str]]:
    """Filter restaurants by city/location with fuzzy matching."""
    messages = []
    if not location:
        return df, messages

    available_cities = get_available_values(df["city"])
    match_result = fuzzy_match_single(location, available_cities)

    if match_result["matched"]:
        matched_city = match_result["result"]
        df = df[df["city"].str.lower() == matched_city.lower()]
        if not match_result["is_exact"]:
            messages.append(match_result["suggestion_message"])
        logger.info(f"Location filter: '{location}' -> '{matched_city}' ({len(df)} results)")
    else:
        messages.append(match_result["suggestion_message"])
        logger.warning(f"Location '{location}' not found in dataset.")
        # Return empty DataFrame — will trigger relaxation
        df = df.iloc[0:0]

    return df, messages


def _filter_by_budget(df: pd.DataFrame, budget: str) -> tuple[pd.DataFrame, list[str]]:
    """Filter restaurants by budget range."""
    messages = []
    if not budget:
        return df, messages

    cost_range = get_cost_range(budget)
    if cost_range is None:
        return df, messages

    min_cost, max_cost = cost_range
    df = df[(df["cost_for_two"] >= min_cost) & (df["cost_for_two"] <= max_cost)]
    logger.info(f"Budget filter: '{budget}' (Rs.{min_cost}-{max_cost}) -> {len(df)} results")

    return df, messages


def _filter_by_cuisine(df: pd.DataFrame, cuisine: str) -> tuple[pd.DataFrame, list[str]]:
    """Filter restaurants by cuisine type with fuzzy matching (EC-2.5)."""
    messages = []
    if not cuisine:
        return df, messages

    available_cuisines = get_available_values(df["cuisines"])
    match_result = fuzzy_match_multi(cuisine, available_cuisines)

    matched_cuisines = match_result["matched_items"]
    messages.extend(match_result["messages"])

    if matched_cuisines:
        # OR-based filtering: restaurant serves ANY of the requested cuisines
        pattern = "|".join([c.lower() for c in matched_cuisines])
        mask = df["cuisines"].str.lower().str.contains(pattern, na=False, regex=True)
        df = df[mask]
        logger.info(
            f"Cuisine filter: {matched_cuisines} -> {len(df)} results"
        )
    else:
        logger.warning(f"No matching cuisines found for '{cuisine}'.")
        df = df.iloc[0:0]

    return df, messages


def _filter_by_rating(df: pd.DataFrame, min_rating: float) -> tuple[pd.DataFrame, list[str]]:
    """Filter restaurants by minimum rating (EC-2.7)."""
    messages = []
    if min_rating <= 0:
        return df, messages

    # Exclude unrated (0.0) restaurants when a rating filter is applied
    df = df[(df["rating"] >= min_rating) & (df["rating"] > 0)]

    if min_rating >= 4.5 and len(df) < 3:
        messages.append(
            f"Very few restaurants have a {min_rating}+ rating. "
            f"Consider lowering your minimum for more options."
        )

    logger.info(f"Rating filter: >= {min_rating} -> {len(df)} results")
    return df, messages


def _sort_and_cap(df: pd.DataFrame, max_results: int = MAX_FILTERED_RESULTS) -> pd.DataFrame:
    """
    Sort by relevance (rating * log(votes+1)) and cap results (EC-2.10).
    """
    if len(df) == 0:
        return df

    import numpy as np

    # Relevance score: rating with vote-count boost
    df = df.copy()
    df["_relevance"] = df["rating"] * np.log1p(df["votes"])
    df = df.sort_values("_relevance", ascending=False).head(max_results)
    df = df.drop(columns=["_relevance"])

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Progressive Relaxation (EC-2.1)
# ---------------------------------------------------------------------------

RELAXATION_ORDER = ["rating", "budget", "cuisine"]


def _apply_filters(
    df: pd.DataFrame,
    preferences: dict,
    skip_filters: set | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Apply all filters except those in skip_filters."""
    skip = skip_filters or set()
    all_messages = []

    # 1. Location (never relaxed — it's the primary filter)
    df, msgs = _filter_by_location(df, preferences.get("location", ""))
    all_messages.extend(msgs)

    # 2. Budget
    if "budget" not in skip:
        df, msgs = _filter_by_budget(df, preferences.get("budget", ""))
        all_messages.extend(msgs)

    # 3. Cuisine
    if "cuisine" not in skip:
        df, msgs = _filter_by_cuisine(df, preferences.get("cuisine", ""))
        all_messages.extend(msgs)

    # 4. Rating
    if "rating" not in skip:
        df, msgs = _filter_by_rating(df, preferences.get("min_rating", 0))
        all_messages.extend(msgs)

    return df, all_messages


def filter_restaurants(preferences: dict) -> FilterResult:
    """
    Main entry point — filter restaurants based on user preferences.

    Applies filters in order: Location → Budget → Cuisine → Rating.
    If no results are found, progressively relaxes filters in order:
    rating → budget → cuisine (EC-2.1).

    Args:
        preferences: Dict with keys: location, budget, cuisine, min_rating, additional_prefs

    Returns:
        FilterResult object with matching restaurants and metadata
    """
    # Load the processed dataset
    df = load_processed_data()
    original_count = len(df)

    logger.info(f"Starting filter pipeline with {original_count} restaurants...")
    logger.info(f"Preferences: {preferences}")

    # Check if any filters are provided (EC-2.8)
    has_filters = any([
        preferences.get("location"),
        preferences.get("budget"),
        preferences.get("cuisine"),
        preferences.get("min_rating", 0) > 0,
    ])

    if not has_filters:
        # No filters — return top-rated restaurants globally
        df = _sort_and_cap(df)
        return FilterResult(
            restaurants=df,
            total_matches=original_count,
            filters_applied={},
            relaxed_filters=[],
            messages=["Showing top restaurants across all locations."],
        )

    # Apply all filters
    filtered_df, messages = _apply_filters(df, preferences)
    relaxed_filters = []

    # Progressive relaxation if no results (EC-2.1)
    if len(filtered_df) == 0:
        logger.info("No results with all filters. Starting progressive relaxation...")

        for filter_to_relax in RELAXATION_ORDER:
            skip = set(relaxed_filters + [filter_to_relax])
            filtered_df, relax_messages = _apply_filters(df, preferences, skip_filters=skip)

            if len(filtered_df) > 0:
                relaxed_filters.append(filter_to_relax)
                relaxed_labels = ", ".join(relaxed_filters)
                messages.append(
                    f"No exact matches found. Showing closest options "
                    f"(relaxed: {relaxed_labels})."
                )
                messages.extend(relax_messages)
                logger.info(
                    f"Found {len(filtered_df)} results after relaxing: {relaxed_labels}"
                )
                break
            else:
                relaxed_filters.append(filter_to_relax)

        # If still no results after all relaxation
        if len(filtered_df) == 0:
            messages.append(
                "No restaurants found matching your preferences. "
                "Try a different location or broaden your search."
            )

    total_matches = len(filtered_df)

    # Sort and cap results (EC-2.10)
    if total_matches > MAX_FILTERED_RESULTS:
        messages.append(
            f"Found {total_matches} restaurants. "
            f"Showing the top {MAX_FILTERED_RESULTS} recommendations."
        )

    filtered_df = _sort_and_cap(filtered_df)

    # Build filters-applied summary
    filters_applied = {}
    if preferences.get("location"):
        filters_applied["location"] = preferences["location"]
    if preferences.get("budget"):
        filters_applied["budget"] = preferences["budget"]
    if preferences.get("cuisine"):
        filters_applied["cuisine"] = preferences["cuisine"]
    if preferences.get("min_rating", 0) > 0:
        filters_applied["min_rating"] = preferences["min_rating"]

    logger.info(
        f"Filter pipeline complete: {total_matches} matches, "
        f"returning top {len(filtered_df)}. "
        f"Relaxed: {relaxed_filters or 'none'}"
    )

    return FilterResult(
        restaurants=filtered_df,
        total_matches=total_matches,
        filters_applied=filters_applied,
        relaxed_filters=relaxed_filters,
        messages=messages,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    # Test with sample preferences
    test_preferences = {
        "location": "Whitefield",
        "budget": "medium",
        "cuisine": "North Indian",
        "min_rating": 3.5,
        "additional_prefs": "",
    }

    print(f"\nTest Preferences: {test_preferences}\n")
    result = filter_restaurants(test_preferences)

    print(f"Total matches: {result.total_matches}")
    print(f"Returned: {len(result.restaurants)}")
    print(f"Relaxed filters: {result.relaxed_filters}")
    print(f"Messages: {result.messages}")
    print(f"\nTop results:")
    if result.has_results:
        display_cols = ["name", "city", "cuisines", "cost_for_two", "rating", "votes"]
        cols = [c for c in display_cols if c in result.restaurants.columns]
        print(result.restaurants[cols].to_string(index=False))
    else:
        print("No results found.")
