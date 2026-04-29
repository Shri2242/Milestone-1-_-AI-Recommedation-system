import sys
import argparse
import logging
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Supress internal info logs from polluting stdout (observability goes to stderr)
logging.getLogger("filtering.filter_engine").setLevel(logging.WARNING)
logging.getLogger("recommendation.recommender").setLevel(logging.WARNING)
logging.getLogger("recommendation.prompt_builder").setLevel(logging.WARNING)
logging.getLogger("recommendation.llm_connector").setLevel(logging.WARNING)
logging.getLogger("data_ingestion.preprocessor").setLevel(logging.WARNING)

from src.phase0.utils import validate_preferences
from src.phase3_recommendation.recommender import get_recommendations
from src.phase5_output.renderer import TerminalRenderer


def run_recommendation(args):
    """Executes the end-to-end pipeline and delegates output to Phase 5 renderer."""
    raw_prefs = {
        "location": args.location,
        "budget": args.budget,
        "cuisine": args.cuisine,
        "min_rating": args.rating,
        "additional_prefs": args.prefs,
    }
    
    prefs = validate_preferences(raw_prefs)
    
    # Phase 2 & 3: Filter and LLM Processing (Orchestrated)
    rec_result = get_recommendations(prefs)
    filter_result = rec_result.filter_result
    
    if not filter_result.has_results:
        # Phase 5: Specific empty state rendering
        TerminalRenderer.render_empty_state(filter_result)
        TerminalRenderer.emit_telemetry(filter_result, rec_result)
        sys.exit(0)

    # Phase 5: Render and Telemetry
    if rec_result.has_results:
        TerminalRenderer.render_recommendations(rec_result)
    else:
        TerminalRenderer.render_empty_state(filter_result, rec_result)
        
    TerminalRenderer.emit_telemetry(filter_result, rec_result)


def main():
    parser = argparse.ArgumentParser(
        description="Phase 5 CLI - Restaurant Recommender",
        prog="milestone1 recommend-run"
    )
    
    parser.add_argument("--location", type=str, default="", help="City or neighborhood (e.g. Indiranagar)")
    parser.add_argument("--budget", type=str, choices=["low", "medium", "high", ""], default="", help="Budget category")
    parser.add_argument("--cuisine", type=str, default="", help="Preferred cuisine")
    parser.add_argument("--rating", type=float, default=0.0, help="Minimum rating (0-5)")
    parser.add_argument("--prefs", type=str, default="", help="Additional preferences for the LLM")

    args = parser.parse_args()
    
    run_recommendation(args)


if __name__ == "__main__":
    main()
