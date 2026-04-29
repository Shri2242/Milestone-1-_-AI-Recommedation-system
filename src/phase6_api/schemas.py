from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class RecommendationRequest(BaseModel):
    """JSON Contract for incoming recommendation requests."""
    location: str = Field(..., max_length=100, description="City or neighborhood")
    budget: Optional[str] = Field("", max_length=20, description="Budget band (e.g. low, medium, high)")
    cuisine: Optional[str] = Field("", max_length=100, description="Preferred cuisine")
    min_rating: Optional[float] = Field(0.0, ge=0.0, le=5.0, description="Minimum rating (0.0 to 5.0)")
    additional_prefs: Optional[str] = Field("", max_length=500, description="Optional extra free-text instructions")


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class RecommendationItem(BaseModel):
    """A single recommended restaurant."""
    id: str
    rank: int
    name: str
    cuisine: str
    rating: float
    cost_for_two: int
    explanation: str


class TelemetryData(BaseModel):
    """Non-sensitive observability metadata for the UI."""
    latency_ms: int
    provider: str
    model: str
    total_candidates: int
    relaxed_filters: List[str]


class RecommendationResponse(BaseModel):
    """JSON Contract for outgoing recommendation results."""
    recommendations: List[RecommendationItem]
    source: str  # e.g., 'llm', 'rule_based', 'no_candidates'
    counts: Dict[str, int]
    telemetry: Optional[TelemetryData] = None
    messages: List[str] = []
