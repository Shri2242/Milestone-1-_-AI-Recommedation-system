"""
Fuzzy Matcher
=============
Handles partial and misspelled user inputs for locations and cuisines
using fuzzy string matching (RapidFuzz library).

Handles edge cases:
- EC-2.2: Misspelled location (e.g., "Bangalor" → "Bangalore")
- EC-2.3: Misspelled cuisine (e.g., "Itlian" → "Italian")
- EC-2.4: Location not in dataset
"""

import logging
from rapidfuzz import fuzz, process

logger = logging.getLogger("filtering.fuzzy_match")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SIMILARITY_THRESHOLD = 70  # Minimum score (0–100) to accept a fuzzy match
MAX_SUGGESTIONS = 5        # Max suggestions to show when no match found


def fuzzy_match_single(
    query: str,
    choices: list[str],
    threshold: int = SIMILARITY_THRESHOLD,
) -> dict:
    """
    Find the best fuzzy match for a single query against a list of choices.

    Args:
        query: User input string (e.g., "Bangalor")
        choices: Valid options to match against
        threshold: Minimum similarity score (0–100)

    Returns:
        Dict with keys:
            - matched: bool — whether a match was found
            - original: str — user's original input
            - result: str — best matching value (or original if exact match)
            - score: float — similarity score
            - is_exact: bool — whether it was an exact match
            - suggestion_message: str — user-facing message
    """
    if not query or not choices:
        return {
            "matched": False,
            "original": query,
            "result": query,
            "score": 0,
            "is_exact": False,
            "suggestion_message": "",
        }

    query_lower = query.strip().lower()

    # Check for exact match first (case-insensitive)
    choices_lower = {c.lower(): c for c in choices}
    if query_lower in choices_lower:
        return {
            "matched": True,
            "original": query,
            "result": choices_lower[query_lower],
            "score": 100,
            "is_exact": True,
            "suggestion_message": "",
        }

    # Fuzzy match
    best_match = process.extractOne(
        query_lower,
        list(choices_lower.keys()),
        scorer=fuzz.WRatio,
    )

    if best_match and best_match[1] >= threshold:
        matched_key = best_match[0]
        matched_value = choices_lower[matched_key]
        score = best_match[1]

        logger.info(
            f"Fuzzy match: '{query}' -> '{matched_value}' (score: {score})"
        )
        return {
            "matched": True,
            "original": query,
            "result": matched_value,
            "score": score,
            "is_exact": False,
            "suggestion_message": f"Showing results for '{matched_value}' (did you mean this?)",
        }

    # No match found — provide suggestions
    top_matches = process.extract(
        query_lower,
        list(choices_lower.keys()),
        scorer=fuzz.WRatio,
        limit=MAX_SUGGESTIONS,
    )
    suggestions = [choices_lower[m[0]] for m in top_matches if m[1] > 30]

    logger.warning(f"No match found for '{query}'. Suggestions: {suggestions}")
    return {
        "matched": False,
        "original": query,
        "result": query,
        "score": 0,
        "is_exact": False,
        "suggestion_message": (
            f"'{query}' not found. "
            f"Did you mean: {', '.join(suggestions)}?"
            if suggestions
            else f"'{query}' not found. No similar options available."
        ),
    }


def fuzzy_match_multi(
    query: str,
    choices: list[str],
    threshold: int = SIMILARITY_THRESHOLD,
) -> dict:
    """
    Match a comma-separated list of values (e.g., multiple cuisines).

    Each item is matched independently. Returns aggregated results.

    Args:
        query: Comma-separated user input (e.g., "Itlian, Chineese")
        choices: Valid options
        threshold: Minimum similarity score

    Returns:
        Dict with keys:
            - matched_items: list of successfully matched values
            - unmatched_items: list of items that couldn't be matched
            - messages: list of user-facing messages
            - all_matched: bool — True if all items were matched
    """
    if not query:
        return {
            "matched_items": [],
            "unmatched_items": [],
            "messages": [],
            "all_matched": True,
        }

    items = [item.strip() for item in query.split(",") if item.strip()]
    matched_items = []
    unmatched_items = []
    messages = []

    for item in items:
        result = fuzzy_match_single(item, choices, threshold)
        if result["matched"]:
            matched_items.append(result["result"])
            if not result["is_exact"]:
                messages.append(result["suggestion_message"])
        else:
            unmatched_items.append(item)
            messages.append(result["suggestion_message"])

    return {
        "matched_items": matched_items,
        "unmatched_items": unmatched_items,
        "messages": messages,
        "all_matched": len(unmatched_items) == 0,
    }


def get_available_values(df_column) -> list[str]:
    """
    Extract unique, sorted values from a DataFrame column.

    For columns with comma-separated values (like cuisines),
    this splits and extracts individual values.

    Args:
        df_column: pandas Series

    Returns:
        Sorted list of unique values
    """
    values = set()
    for val in df_column.dropna().unique():
        for item in str(val).split(","):
            cleaned = item.strip()
            if cleaned and cleaned.lower() != "nan":
                values.add(cleaned)
    return sorted(values)
