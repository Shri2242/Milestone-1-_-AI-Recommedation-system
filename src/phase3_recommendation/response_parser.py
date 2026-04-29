"""
Response Parser
===============
Parses and validates LLM responses into structured recommendation objects.

Handles edge cases:
- EC-3.2: LLM returns invalid JSON
- EC-3.3: LLM hallucinates restaurant names
- EC-3.4: LLM returns fewer than requested recommendations
- EC-3.8: Biased or inappropriate LLM output (basic content filter)
"""

import re
import json
import logging

logger = logging.getLogger("recommendation.response_parser")

# ---------------------------------------------------------------------------
# Content filter keywords (EC-3.8)
# ---------------------------------------------------------------------------
BLOCKED_KEYWORDS = [
    "offensive", "inappropriate",  # placeholders for actual filter list
]


class Recommendation:
    """A single parsed restaurant recommendation."""

    def __init__(
        self,
        rank: int,
        name: str,
        cuisine: str,
        rating: float,
        cost_for_two: int,
        explanation: str,
    ):
        self.rank = rank
        self.name = name
        self.cuisine = cuisine
        self.rating = rating
        self.cost_for_two = cost_for_two
        self.explanation = explanation

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "name": self.name,
            "cuisine": self.cuisine,
            "rating": self.rating,
            "cost_for_two": self.cost_for_two,
            "explanation": self.explanation,
        }


class ParseResult:
    """Result of parsing an LLM response."""

    def __init__(
        self,
        recommendations: list[Recommendation],
        raw_response: str,
        parse_success: bool,
        hallucinated_names: list[str],
        messages: list[str],
    ):
        self.recommendations = recommendations
        self.raw_response = raw_response
        self.parse_success = parse_success
        self.hallucinated_names = hallucinated_names
        self.messages = messages

    @property
    def has_results(self) -> bool:
        return len(self.recommendations) > 0

    def to_dict_list(self) -> list[dict]:
        return [r.to_dict() for r in self.recommendations]


def _extract_json(text: str) -> str | None:
    """
    Extract JSON array from LLM response text.
    Handles responses wrapped in markdown code blocks, extra text, etc.

    Args:
        text: Raw LLM response

    Returns:
        JSON string or None if not found
    """
    if not text:
        return None

    # Try 1: Find JSON array directly
    # Look for the outermost [...] in the text
    bracket_start = text.find("[")
    bracket_end = text.rfind("]")

    if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
        candidate = text[bracket_start : bracket_end + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # Try 2: Extract from markdown code block
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            json.loads(match.strip())
            return match.strip()
        except json.JSONDecodeError:
            continue

    # Try 3: The entire response might be valid JSON
    try:
        json.loads(text.strip())
        return text.strip()
    except json.JSONDecodeError:
        pass

    return None


def _validate_against_data(
    recommendations: list[dict],
    valid_restaurants: list[dict],
) -> tuple[list[dict], list[str]]:
    """
    Cross-validate LLM recommendations against the actual filtered data (EC-3.3).

    Removes any hallucinated restaurant names that don't exist in the data.

    Args:
        recommendations: Parsed recommendation dicts from LLM
        valid_restaurants: Original filtered restaurant list

    Returns:
        Tuple of (validated recommendations, hallucinated names)
    """
    valid_names = {r["name"].strip().lower() for r in valid_restaurants}
    validated = []
    hallucinated = []

    for rec in recommendations:
        rec_name = rec.get("name", "").strip().lower()
        if rec_name in valid_names:
            validated.append(rec)
        else:
            # Try fuzzy match — LLM might slightly alter the name
            from rapidfuzz import fuzz
            best_score = 0
            best_match = None
            for vname in valid_names:
                score = fuzz.ratio(rec_name, vname)
                if score > best_score:
                    best_score = score
                    best_match = vname

            if best_score >= 85:
                # Close enough — fix the name
                for vr in valid_restaurants:
                    if vr["name"].strip().lower() == best_match:
                        rec["name"] = vr["name"]
                        break
                validated.append(rec)
                logger.info(f"Fuzzy-corrected LLM name: '{rec_name}' -> '{best_match}'")
            else:
                hallucinated.append(rec.get("name", "Unknown"))
                logger.warning(f"Hallucinated restaurant removed: '{rec.get('name', 'Unknown')}'")

    return validated, hallucinated


def _content_filter(text: str) -> bool:
    """
    Basic content filter for LLM output (EC-3.8).

    Returns True if content passes the filter (is safe).
    """
    text_lower = text.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in text_lower:
            logger.warning(f"Content filter triggered on keyword: '{keyword}'")
            return False
    return True


def parse_llm_response(
    raw_response: str,
    valid_restaurants: list[dict],
    num_requested: int = 5,
) -> ParseResult:
    """
    Parse and validate an LLM response into structured recommendations.

    Args:
        raw_response: Raw text response from the LLM
        valid_restaurants: Original filtered restaurant data for validation
        num_requested: How many recommendations were requested

    Returns:
        ParseResult object
    """
    messages = []

    # Content filter (EC-3.8)
    if not _content_filter(raw_response):
        logger.warning("LLM response failed content filter.")
        return ParseResult(
            recommendations=[],
            raw_response=raw_response,
            parse_success=False,
            hallucinated_names=[],
            messages=["Response filtered due to content policy."],
        )

    # Extract JSON from response (EC-3.2)
    json_str = _extract_json(raw_response)

    if json_str is None:
        logger.error("Failed to extract JSON from LLM response.")
        logger.debug(f"Raw response: {raw_response[:500]}")
        return ParseResult(
            recommendations=[],
            raw_response=raw_response,
            parse_success=False,
            hallucinated_names=[],
            messages=["Could not parse AI response. Using fallback ranking."],
        )

    # Parse JSON
    try:
        rec_list = json.loads(json_str)
        if not isinstance(rec_list, list):
            raise ValueError("Expected a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"JSON parse error: {e}")
        return ParseResult(
            recommendations=[],
            raw_response=raw_response,
            parse_success=False,
            hallucinated_names=[],
            messages=["Could not parse AI response format. Using fallback ranking."],
        )

    # Validate against actual data (EC-3.3)
    validated, hallucinated = _validate_against_data(rec_list, valid_restaurants)

    if hallucinated:
        messages.append(
            f"Removed {len(hallucinated)} AI-generated entries not in our database."
        )

    # Check if fewer than requested (EC-3.4)
    if len(validated) < num_requested and len(validated) > 0:
        messages.append(
            f"AI recommended {len(validated)} restaurants "
            f"(requested {num_requested})."
        )

    # Build Recommendation objects
    recommendations = []
    for i, rec in enumerate(validated, start=1):
        try:
            recommendations.append(
                Recommendation(
                    rank=i,
                    name=rec.get("name", "Unknown"),
                    cuisine=rec.get("cuisine", "N/A"),
                    rating=float(rec.get("rating", 0)),
                    cost_for_two=int(rec.get("cost_for_two", 0)),
                    explanation=rec.get("explanation", "Recommended based on your preferences."),
                )
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping malformed recommendation: {e}")

    logger.info(
        f"Parsed {len(recommendations)} valid recommendations "
        f"({len(hallucinated)} hallucinated removed)"
    )

    return ParseResult(
        recommendations=recommendations,
        raw_response=raw_response,
        parse_success=True,
        hallucinated_names=hallucinated,
        messages=messages,
    )
