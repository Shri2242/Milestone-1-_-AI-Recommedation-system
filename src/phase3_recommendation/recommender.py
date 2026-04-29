"""
Recommender — Orchestrator
==========================
Orchestrates the full recommendation flow:
  User Preferences → Filter Engine → Prompt Builder → LLM → Parser → Results

Includes rule-based fallback when the LLM is unavailable or fails.

Handles edge cases:
- EC-3.1: LLM API Timeout (fallback)
- EC-3.2: Invalid JSON (retry + fallback)
- EC-3.4: Fewer results than requested (supplement with rule-based)
- EC-3.7: Provider failover (handled by llm_connector)
"""

import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.phase0.config import MAX_RECOMMENDATIONS, LLM_PROVIDER
from src.phase2_filtering.filter_engine import filter_restaurants, FilterResult
from src.phase3_recommendation.prompt_builder import build_prompt
from src.phase3_recommendation.llm_connector import generate_completion, get_provider
from src.phase3_recommendation.response_parser import (
    parse_llm_response,
    Recommendation,
    ParseResult,
)

logger = logging.getLogger("recommendation.recommender")

MAX_LLM_RETRIES = 1  # Retry once on parse failure


# ---------------------------------------------------------------------------
# Rule-Based Fallback
# ---------------------------------------------------------------------------

def _rule_based_ranking(
    filter_result: FilterResult,
    num_recommendations: int = MAX_RECOMMENDATIONS,
) -> list[Recommendation]:
    """
    Generate recommendations using rule-based ranking (no LLM).

    Used as a fallback when the LLM is unavailable or returns bad output.
    Ranks by: rating (desc) → votes (desc) → cost relevance.

    Args:
        filter_result: FilterResult from the filter engine
        num_recommendations: Number of recommendations to generate

    Returns:
        List of Recommendation objects
    """
    if not filter_result.has_results:
        return []

    df = filter_result.restaurants.copy()

    # Already sorted by relevance from filter engine
    recommendations = []
    for i, (_, row) in enumerate(df.head(num_recommendations).iterrows(), start=1):
        # Generate a simple explanation
        highlights = []
        rating = row.get("rating", 0)
        votes = row.get("votes", 0)
        cost = row.get("cost_for_two", 0)

        if rating >= 4.5:
            highlights.append("exceptional rating")
        elif rating >= 4.0:
            highlights.append("highly rated")

        if votes >= 1000:
            highlights.append("very popular")
        elif votes >= 500:
            highlights.append("popular choice")

        if cost <= 500:
            highlights.append("budget-friendly")
        elif cost >= 1500:
            highlights.append("premium dining")

        if row.get("has_online_delivery"):
            highlights.append("offers online delivery")

        explanation = (
            f"Rated {rating}/5 with {votes} votes. "
            + (", ".join(highlights).capitalize() + "." if highlights else "A solid choice based on your preferences.")
        )

        recommendations.append(
            Recommendation(
                rank=i,
                name=row.get("name", "Unknown"),
                cuisine=row.get("cuisines", "N/A"),
                rating=float(rating),
                cost_for_two=int(cost),
                explanation=explanation,
            )
        )

    logger.info(f"Rule-based fallback generated {len(recommendations)} recommendations.")
    return recommendations


# ---------------------------------------------------------------------------
# Main Recommendation Flow
# ---------------------------------------------------------------------------

class RecommendationResult:
    """Final result of the recommendation pipeline."""

    def __init__(
        self,
        recommendations: list[Recommendation],
        preferences: dict,
        filter_result: FilterResult,
        source: str,  # "llm" or "rule_based"
        llm_provider: str = "",
        llm_model: str = "",
        latency_ms: int = 0,
        messages: list[str] = None,
    ):
        self.recommendations = recommendations
        self.preferences = preferences
        self.filter_result = filter_result
        self.source = source
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.latency_ms = latency_ms
        self.messages = messages or []

    @property
    def has_results(self) -> bool:
        return len(self.recommendations) > 0

    @property
    def is_ai_powered(self) -> bool:
        return self.source == "llm"

    def to_dict_list(self) -> list[dict]:
        return [r.to_dict() for r in self.recommendations]


def get_recommendations(preferences: dict) -> RecommendationResult:
    """
    Main entry point — generate restaurant recommendations.

    Flow:
    1. Filter restaurants based on preferences (Phase 2)
    2. Build LLM prompt with filtered data
    3. Call LLM for intelligent ranking + explanations
    4. Parse and validate LLM response
    5. Fall back to rule-based ranking if LLM fails

    Args:
        preferences: Dict with keys: location, budget, cuisine, min_rating, additional_prefs

    Returns:
        RecommendationResult with ranked recommendations
    """
    all_messages = []

    # --- Step 1: Filter restaurants ---
    logger.info("Step 1: Filtering restaurants...")
    filter_result = filter_restaurants(preferences)
    all_messages.extend(filter_result.messages)

    if not filter_result.has_results:
        logger.warning("No restaurants found after filtering.")
        return RecommendationResult(
            recommendations=[],
            preferences=preferences,
            filter_result=filter_result,
            source="rule_based",
            messages=all_messages,
        )

    # --- Step 2: Check if LLM is available ---
    provider = get_provider()
    if provider is None:
        logger.info("No LLM provider available. Using rule-based fallback.")
        all_messages.append("AI recommendations unavailable. Showing top picks based on ratings.")
        recommendations = _rule_based_ranking(filter_result, MAX_RECOMMENDATIONS)
        return RecommendationResult(
            recommendations=recommendations,
            preferences=preferences,
            filter_result=filter_result,
            source="rule_based",
            messages=all_messages,
        )

    # --- Step 3: Build prompt ---
    logger.info("Step 2: Building LLM prompt...")
    restaurant_data = filter_result.to_dict_list()
    model_name = getattr(provider, "model", "gpt-3.5-turbo")

    prompt = build_prompt(
        preferences=preferences,
        restaurants=restaurant_data,
        model_name=model_name,
        num_recommendations=MAX_RECOMMENDATIONS,
    )

    if prompt["was_truncated"]:
        all_messages.append("Some lower-rated restaurants were excluded to fit the AI's context window.")

    # --- Step 4: Call LLM (with retry) ---
    llm_response = None
    parse_result = None

    for attempt in range(1, MAX_LLM_RETRIES + 2):  # +2 because range is exclusive
        logger.info(f"Step 3: Calling LLM (attempt {attempt})...")
        llm_response = provider.generate(prompt["system_prompt"], prompt["user_prompt"])

        if not llm_response.success:
            logger.error(f"LLM call failed: {llm_response.error}")
            if attempt <= MAX_LLM_RETRIES:
                logger.info("Retrying...")
                continue
            break

        # --- Step 5: Parse response ---
        logger.info("Step 4: Parsing LLM response...")
        parse_result = parse_llm_response(
            raw_response=llm_response.content,
            valid_restaurants=restaurant_data,
            num_requested=MAX_RECOMMENDATIONS,
        )

        if parse_result.has_results:
            all_messages.extend(parse_result.messages)
            break
        else:
            logger.warning(f"Parse attempt {attempt} yielded no results.")
            if attempt <= MAX_LLM_RETRIES:
                logger.info("Retrying with LLM...")

    # --- Step 6: Check results or fallback ---
    if parse_result and parse_result.has_results:
        recommendations = parse_result.recommendations

        # Supplement with rule-based picks if fewer than requested (EC-3.4)
        if len(recommendations) < MAX_RECOMMENDATIONS:
            existing_names = {r.name.lower() for r in recommendations}
            fallback_recs = _rule_based_ranking(filter_result, MAX_RECOMMENDATIONS * 2)
            for fb_rec in fallback_recs:
                if fb_rec.name.lower() not in existing_names:
                    fb_rec.rank = len(recommendations) + 1
                    fb_rec.explanation = "(Based on ratings) " + fb_rec.explanation
                    recommendations.append(fb_rec)
                    existing_names.add(fb_rec.name.lower())
                    if len(recommendations) >= MAX_RECOMMENDATIONS:
                        break

            if len(recommendations) > len(parse_result.recommendations):
                all_messages.append(
                    "Additional picks based on ratings included to fill recommendations."
                )

        logger.info(f"LLM-powered recommendations: {len(recommendations)} results.")
        return RecommendationResult(
            recommendations=recommendations,
            preferences=preferences,
            filter_result=filter_result,
            source="llm",
            llm_provider=llm_response.provider if llm_response else "",
            llm_model=llm_response.model if llm_response else "",
            latency_ms=llm_response.latency_ms if llm_response else 0,
            messages=all_messages,
        )

    # Fallback to rule-based
    logger.warning("LLM failed. Falling back to rule-based ranking.")
    all_messages.append(
        "AI recommendations are currently unavailable. "
        "Showing top picks based on ratings and popularity."
    )
    recommendations = _rule_based_ranking(filter_result, MAX_RECOMMENDATIONS)

    return RecommendationResult(
        recommendations=recommendations,
        preferences=preferences,
        filter_result=filter_result,
        source="rule_based",
        llm_provider=llm_response.provider if llm_response else "",
        llm_model=llm_response.model if llm_response else "",
        messages=all_messages,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    test_preferences = {
        "location": "Whitefield",
        "budget": "medium",
        "cuisine": "North Indian",
        "min_rating": 3.5,
        "additional_prefs": "",
    }

    print(f"\nPreferences: {test_preferences}\n")
    result = get_recommendations(test_preferences)

    print(f"Source: {result.source}")
    print(f"Provider: {result.llm_provider or 'N/A'}")
    print(f"Latency: {result.latency_ms}ms")
    print(f"Messages: {result.messages}")
    print(f"\nRecommendations ({len(result.recommendations)}):")
    for rec in result.recommendations:
        print(f"  #{rec.rank} {rec.name}")
        print(f"     {rec.cuisine} | Rating: {rec.rating} | Rs.{rec.cost_for_two}")
        print(f"     {rec.explanation}")
        print()
