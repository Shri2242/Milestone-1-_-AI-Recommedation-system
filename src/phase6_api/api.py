import sys
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.phase0.config import GROQ_API_KEY
from src.phase0.utils import validate_preferences
from src.phase3_recommendation.recommender import get_recommendations
from src.phase6_api.schemas import (
    RecommendationRequest, 
    RecommendationResponse, 
    RecommendationItem,
    TelemetryData
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(
    title="Milestone 1 - Restaurant Recommender API",
    description="Phase 6 Backend HTTP API",
    version="1.0.0"
)

# CORS restricted to typical dev frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Process up, keys configured (without exposing values)."""
    return {
        "status": "ok",
        "llm_configured": bool(GROQ_API_KEY and GROQ_API_KEY != "your-groq-api-key-here")
    }


@app.post("/api/v1/recommendations", response_model=RecommendationResponse)
def get_restaurant_recommendations(req: RecommendationRequest):
    """
    Validate input, run load_restaurants, recommend_with_groq, return DTOs.
    """
    # 1. Map to Phase 2 preference structure and validate
    raw_prefs = {
        "location": req.location,
        "budget": req.budget,
        "cuisine": req.cuisine,
        "min_rating": req.min_rating,
        "additional_prefs": req.additional_prefs,
    }
    
    prefs = validate_preferences(raw_prefs)
    
    # 2. Orchestrate filtering + LLM (Phase 2 & 3)
    try:
        rec_result = get_recommendations(prefs)
    except Exception as e:
        logger.error(f"Internal Pipeline Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error")

    # 3. Map to DTOs
    items = []
    for r in rec_result.recommendations:
        items.append(RecommendationItem(
            id=str(r.rank), # Use rank as temporary ID
            rank=r.rank,
            name=r.name,
            cuisine=r.cuisine,
            rating=r.rating,
            cost_for_two=r.cost_for_two,
            explanation=r.explanation
        ))

    telemetry = TelemetryData(
        latency_ms=rec_result.latency_ms,
        provider=rec_result.llm_provider,
        model=rec_result.llm_model,
        total_candidates=rec_result.filter_result.total_matches,
        relaxed_filters=rec_result.filter_result.relaxed_filters
    )

    source = rec_result.source
    if not rec_result.has_results:
        source = "no_candidates"

    return RecommendationResponse(
        recommendations=items,
        source=source,
        counts={
            "returned": len(items),
            "candidates": rec_result.filter_result.total_matches
        },
        telemetry=telemetry,
        messages=rec_result.messages
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
