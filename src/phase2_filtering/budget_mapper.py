"""
Budget Mapper
=============
Maps budget labels (Low / Medium / High) to cost-for-two ranges
based on the actual dataset distribution.

Budget Mapping Strategy (from phased-architecture.md):
  Low    → 0 – 500 INR
  Medium → 500 – 1,500 INR
  High   → 1,500+ INR
"""

import logging

logger = logging.getLogger("filtering.budget_mapper")

# ---------------------------------------------------------------------------
# Budget → Cost Range mapping
# ---------------------------------------------------------------------------
BUDGET_RANGES = {
    "low": (0, 500),
    "medium": (500, 1500),
    "high": (1500, float("inf")),
}

# For display purposes
BUDGET_LABELS = {
    "low": "Under Rs.500",
    "medium": "Rs.500 - Rs.1,500",
    "high": "Rs.1,500+",
}


def get_cost_range(budget_label: str) -> tuple[int, float] | None:
    """
    Convert a budget label to a (min_cost, max_cost) range.

    Args:
        budget_label: One of "low", "medium", "high" (case-insensitive)

    Returns:
        Tuple of (min_cost, max_cost) or None if label is empty/invalid
    """
    if not budget_label:
        return None

    budget_label = budget_label.strip().lower()

    if budget_label in BUDGET_RANGES:
        cost_range = BUDGET_RANGES[budget_label]
        logger.debug(f"Budget '{budget_label}' mapped to cost range {cost_range}")
        return cost_range

    logger.warning(f"Unknown budget label: '{budget_label}'. Ignoring budget filter.")
    return None


def get_budget_label(cost: int) -> str:
    """
    Determine the budget category for a given cost value.

    Args:
        cost: Cost for two in INR

    Returns:
        Budget label string: "Low", "Medium", or "High"
    """
    if cost <= 500:
        return "Low"
    elif cost <= 1500:
        return "Medium"
    else:
        return "High"


def get_display_label(budget_label: str) -> str:
    """
    Get a human-readable display string for a budget label.

    Args:
        budget_label: One of "low", "medium", "high"

    Returns:
        Display string like "Under Rs.500"
    """
    return BUDGET_LABELS.get(budget_label.strip().lower(), budget_label)
