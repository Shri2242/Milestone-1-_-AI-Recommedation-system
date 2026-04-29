"""
Utility Functions
=================
Shared helper functions used across the application.

Handles edge cases:
- EC-2.9: Input sanitization (XSS / injection prevention)
- EC-X.4: Unicode / non-English input handling
"""

import re
import html
import logging

logger = logging.getLogger("utils")


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks (EC-2.9).

    - Strips HTML tags
    - Escapes special HTML characters
    - Removes potentially dangerous characters
    - Trims whitespace

    Args:
        text: Raw user input string

    Returns:
        Sanitized string safe for processing
    """
    if not text:
        return ""

    # Strip HTML tags
    cleaned = re.sub(r"<[^>]*>", "", text)

    # Escape HTML entities
    cleaned = html.escape(cleaned)

    # Remove control characters but keep Unicode letters (EC-X.4)
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)

    # Trim whitespace
    cleaned = cleaned.strip()

    return cleaned


def format_currency(amount: int | float, symbol: str = "₹") -> str:
    """
    Format a numeric amount as Indian currency.

    Args:
        amount: The numeric amount
        symbol: Currency symbol (default: ₹)

    Returns:
        Formatted currency string (e.g., "₹1,500")
    """
    try:
        return f"{symbol}{int(amount):,}"
    except (ValueError, TypeError):
        return f"{symbol}N/A"


def format_rating(rating: float) -> str:
    """
    Format a rating value with a star indicator.

    Args:
        rating: Rating value (0.0 - 5.0)

    Returns:
        Formatted rating string (e.g., "⭐ 4.2 / 5.0")
    """
    try:
        rating = float(rating)
        if rating <= 0:
            return "Unrated"
        return f"⭐ {rating:.1f} / 5.0"
    except (ValueError, TypeError):
        return "Unrated"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length with ellipsis.

    Args:
        text: Input text
        max_length: Maximum character length

    Returns:
        Truncated text with "..." if it exceeded max_length
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def parse_cuisines(cuisine_string: str) -> list[str]:
    """
    Parse a comma-separated cuisine string into a clean list.

    Args:
        cuisine_string: e.g., "Italian, Chinese, North Indian"

    Returns:
        List of trimmed cuisine names: ["Italian", "Chinese", "North Indian"]
    """
    if not cuisine_string:
        return []
    return [c.strip() for c in cuisine_string.split(",") if c.strip()]


def validate_preferences(preferences: dict) -> dict:
    """
    Validate and sanitize a user preferences dictionary.

    Args:
        preferences: Raw user input dict with keys like
                     location, budget, cuisine, min_rating, additional_prefs

    Returns:
        Dict with sanitized values and any validation errors
    """
    errors = []
    sanitized = {}

    # Location
    location = sanitize_input(preferences.get("location", ""))
    sanitized["location"] = location

    # Budget
    budget = sanitize_input(preferences.get("budget", "")).lower()
    valid_budgets = ["low", "medium", "high", ""]
    if budget not in valid_budgets:
        errors.append(f"Invalid budget: '{budget}'. Choose from: Low, Medium, High.")
        budget = ""
    sanitized["budget"] = budget

    # Cuisine
    cuisine = sanitize_input(preferences.get("cuisine", ""))
    sanitized["cuisine"] = cuisine

    # Minimum rating
    try:
        min_rating = float(preferences.get("min_rating", 0))
        if min_rating < 0:
            min_rating = 0
        elif min_rating > 5:
            min_rating = 5
            errors.append("Rating capped at 5.0")
    except (ValueError, TypeError):
        min_rating = 0
        errors.append("Invalid rating value. Using 0 (no minimum).")
    sanitized["min_rating"] = min_rating

    # Additional preferences
    additional = sanitize_input(preferences.get("additional_prefs", ""))
    sanitized["additional_prefs"] = additional

    sanitized["errors"] = errors
    return sanitized
