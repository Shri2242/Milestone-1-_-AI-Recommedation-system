"""
Flask Web Application — Entry Point
====================================
Basic Web UI for collecting user preferences and displaying
restaurant recommendations.

Phase 0: Form input + console logging of submitted preferences.
"""

import json
import logging
from flask import Flask, render_template, request, redirect, url_for, flash

from src.phase0.config import (
    APP_HOST,
    APP_PORT,
    FLASK_DEBUG,
    PROJECT_ROOT,
    validate_config,
    get_config_summary,
)
from src.phase0.utils import validate_preferences
from src.phase3_recommendation.recommender import get_recommendations

# Overriding UI paths for Phase 4
PHASE4_DIR = PROJECT_ROOT / "src" / "phase4_ui"
TEMPLATES_DIR = PHASE4_DIR / "templates"
STATIC_DIR = PHASE4_DIR / "static"

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
)
app.secret_key = "dev-secret-key-change-in-production"

logger = logging.getLogger("app")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    """Render the user preferences input form."""
    return render_template("index.html")


@app.route("/recommend", methods=["POST"])
def recommend():
    """
    Process user preferences and display recommendations.

    Phase 0: Validates input, logs to console, and shows a confirmation page.
    Phase 3+: Will integrate with filtering engine and LLM.
    """
    # Collect raw input from form
    raw_preferences = {
        "location": request.form.get("location", ""),
        "budget": request.form.get("budget", ""),
        "cuisine": request.form.get("cuisine", ""),
        "min_rating": request.form.get("min_rating", "0"),
        "additional_prefs": request.form.get("additional_prefs", ""),
    }

    # Validate and sanitize (EC-2.9, EC-2.8)
    validated = validate_preferences(raw_preferences)

    # Log preferences to console
    logger.info("=" * 60)
    logger.info("USER PREFERENCES RECEIVED")
    logger.info("=" * 60)
    logger.info(json.dumps(validated, indent=2))

    # Show validation errors if any
    if validated.get("errors"):
        for error in validated["errors"]:
            flash(error, "warning")

    # Check if at least one preference is provided (EC-2.8)
    has_input = any([
        validated["location"],
        validated["budget"],
        validated["cuisine"],
        validated["min_rating"] > 0,
        validated["additional_prefs"],
    ])

    if not has_input:
        flash("Please provide at least one preference to get recommendations.", "warning")
        return redirect(url_for("index"))

    # Phase 4: Full End-to-End Execution
    logger.info("Executing recommendation engine pipeline...")
    result = get_recommendations(validated)
    
    if result.messages:
        for msg in result.messages:
            flash(msg, "info" if "reservations" not in msg else "warning")

    return render_template("results.html", preferences=validated, result=result)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "Restaurant Recommendation System is running"}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Start the Flask application."""
    logger.info("Starting AI Restaurant Recommendation System...")

    # Validate configuration
    config_ok = validate_config()
    if not config_ok:
        logger.warning("Some configuration issues detected. Check warnings above.")

    logger.info(f"Configuration: {json.dumps(get_config_summary(), indent=2)}")
    logger.info(f"Server starting at http://{APP_HOST}:{APP_PORT}")

    app.run(host=APP_HOST, port=APP_PORT, debug=FLASK_DEBUG)


if __name__ == "__main__":
    main()
