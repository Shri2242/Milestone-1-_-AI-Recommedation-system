import sys
import json
from src.phase2_filtering.filter_engine import FilterResult
from src.phase3_recommendation.recommender import RecommendationResult

class TerminalRenderer:
    """Handles rendering of recommendations and telemetry for the CLI."""

    @staticmethod
    def render_empty_state(filter_result: FilterResult, rec_result: RecommendationResult | None = None):
        """Prints distinct empty state copy based on where the pipeline failed."""
        print("\n" + "="*50)
        if not filter_result.has_results:
            print("[X] No restaurants match filters")
            print("Try broadening your location, budget, or rating constraints.")
        elif rec_result and not rec_result.has_results:
            print("[!] LLM could not justify picks")
            print("The model reviewed the candidates but determined none were a suitable match for your preferences.")
        else:
            print("[?] Unknown error resulted in no recommendations.")
        print("="*50 + "\n")

    @staticmethod
    def render_recommendations(result: RecommendationResult):
        """Prints recommendations in readable markdown/plain format."""
        print("\n" + "="*50)
        print("    TOP RECOMMENDATIONS")
        print("="*50 + "\n")

        for rec in result.recommendations:
            print(f"### #{rec.rank} {rec.name}")
            print(f"**Cuisine:** {rec.cuisine}")
            print(f"**Rating:** {rec.rating} / 5.0")
            print(f"**Estimated Cost:** Rs.{rec.cost_for_two} for two")
            print(f"\n> **AI Explanation:** {rec.explanation}\n")
            print("-" * 50 + "\n")

    @staticmethod
    def emit_telemetry(filter_result: FilterResult, rec_result: RecommendationResult | None = None):
        """
        Observability (light): Log latency, token usage if available, 
        and filter counts to stderr as JSON.
        """
        telemetry = {
            "filters": {
                "total_candidates": filter_result.total_matches,
                "filters_applied": filter_result.filters_applied,
                "relaxed_filters": filter_result.relaxed_filters
            },
            "llm": {
                "provider": rec_result.llm_provider if rec_result else None,
                "model": rec_result.llm_model if rec_result else None,
                "source": rec_result.source if rec_result else "none",
                "latency_ms": rec_result.latency_ms if rec_result else 0,
            }
        }
        
        # Dump to stderr so it doesn't pollute stdout pipes
        print(json.dumps(telemetry, indent=2), file=sys.stderr)
