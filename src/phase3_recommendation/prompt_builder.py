"""
Prompt Builder
==============
Constructs structured LLM prompts from filtered restaurant data
and user preferences.

Handles edge cases:
- EC-3.6: Prompt token limit exceeded (truncation logic)
"""

import logging
from typing import Any

logger = logging.getLogger("recommendation.prompt_builder")

# ---------------------------------------------------------------------------
# Token estimation (rough: 1 token ~ 4 characters for English text)
# ---------------------------------------------------------------------------
CHARS_PER_TOKEN = 4

# Conservative token budgets per model family
TOKEN_LIMITS = {
    "gpt-3.5-turbo": 4000,
    "gpt-4": 7000,
    "gpt-4o": 12000,
    "gpt-4o-mini": 12000,
    "gemini-pro": 8000,
    "gemini-1.5-flash": 12000,
    "llama3": 6000,
}

DEFAULT_TOKEN_LIMIT = 4000

# Base prompt template (without restaurant data) — roughly ~300 tokens
SYSTEM_PROMPT = """You are an expert restaurant recommendation assistant. \
You help users find the best dining options based on their preferences. \
You provide clear, concise, and helpful recommendations with explanations."""

RECOMMENDATION_PROMPT_TEMPLATE = """A user is looking for restaurant recommendations with these preferences:
- Location: {location}
- Budget: {budget}
- Cuisine: {cuisine}
- Minimum Rating: {min_rating}
- Additional Preferences: {additional_prefs}

Here are the matching restaurants from our database:

{restaurant_data}

Based on the above data and the user's preferences, please:
1. Rank the top {num_recommendations} restaurants from the list above.
2. For each restaurant, explain WHY it's a good fit for this user.
3. Highlight any standout features (exceptional rating, great value, unique cuisine).

IMPORTANT RULES:
- ONLY recommend restaurants from the list above. Do NOT invent or hallucinate restaurant names.
- Use the EXACT restaurant names as shown in the data.
- Keep explanations concise (1-2 sentences each).

Respond ONLY with valid JSON in this exact format (no markdown, no backticks):
[
  {{
    "rank": 1,
    "name": "Exact Restaurant Name From Data",
    "cuisine": "Cuisine Type",
    "rating": 4.5,
    "cost_for_two": 800,
    "explanation": "Brief explanation of why this is recommended."
  }}
]"""


def _estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string."""
    return len(text) // CHARS_PER_TOKEN


def _format_restaurant_row(row: dict) -> str:
    """Format a single restaurant as a compact text line."""
    name = row.get("name", "Unknown")
    cuisine = row.get("cuisines", "N/A")
    rating = row.get("rating", 0)
    cost = row.get("cost_for_two", 0)
    votes = row.get("votes", 0)

    online = "Yes" if row.get("has_online_delivery") else "No"
    booking = "Yes" if row.get("has_table_booking") else "No"

    return (
        f"- {name} | Cuisine: {cuisine} | Rating: {rating}/5 | "
        f"Cost for Two: Rs.{cost} | Votes: {votes} | "
        f"Online Delivery: {online} | Table Booking: {booking}"
    )


def build_prompt(
    preferences: dict,
    restaurants: list[dict],
    model_name: str = "gpt-3.5-turbo",
    num_recommendations: int = 5,
) -> dict:
    """
    Build a structured LLM prompt from preferences and filtered restaurants.

    Handles EC-3.6 by truncating restaurant data if the prompt would
    exceed the model's token limit.

    Args:
        preferences: User preferences dict
        restaurants: List of restaurant dicts from the filter engine
        model_name: Name of the LLM model (for token limit lookup)
        num_recommendations: Number of recommendations to request

    Returns:
        Dict with keys:
            - system_prompt: str
            - user_prompt: str
            - restaurant_count: int (how many restaurants were included)
            - was_truncated: bool
            - estimated_tokens: int
    """
    token_limit = TOKEN_LIMITS.get(model_name, DEFAULT_TOKEN_LIMIT)

    # Reserve tokens for system prompt and response
    system_tokens = _estimate_tokens(SYSTEM_PROMPT)
    response_reserve = 800  # Reserve for the LLM's response
    available_tokens = token_limit - system_tokens - response_reserve

    # Format restaurant data, truncating if needed (EC-3.6)
    restaurant_lines = []
    total_chars = 0
    was_truncated = False

    for restaurant in restaurants:
        line = _format_restaurant_row(restaurant)
        line_tokens = _estimate_tokens(line)

        # Check if adding this line would exceed the budget
        if _estimate_tokens("\n".join(restaurant_lines + [line])) > (available_tokens * CHARS_PER_TOKEN):
            was_truncated = True
            logger.warning(
                f"Truncating restaurant data to fit token limit. "
                f"Included {len(restaurant_lines)}/{len(restaurants)} restaurants."
            )
            break

        restaurant_lines.append(line)

    restaurant_data = "\n".join(restaurant_lines) if restaurant_lines else "No restaurants found."

    # Adjust num_recommendations to not exceed available restaurants
    actual_recs = min(num_recommendations, len(restaurant_lines))

    # Build the user prompt
    user_prompt = RECOMMENDATION_PROMPT_TEMPLATE.format(
        location=preferences.get("location", "Any"),
        budget=preferences.get("budget", "Any").capitalize() if preferences.get("budget") else "Any",
        cuisine=preferences.get("cuisine", "Any"),
        min_rating=preferences.get("min_rating", 0),
        additional_prefs=preferences.get("additional_prefs", "None"),
        restaurant_data=restaurant_data,
        num_recommendations=actual_recs,
    )

    estimated_tokens = _estimate_tokens(SYSTEM_PROMPT + user_prompt)

    logger.info(
        f"Prompt built: {len(restaurant_lines)} restaurants, "
        f"~{estimated_tokens} tokens, truncated={was_truncated}"
    )

    return {
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": user_prompt,
        "restaurant_count": len(restaurant_lines),
        "was_truncated": was_truncated,
        "estimated_tokens": estimated_tokens,
    }
