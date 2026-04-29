"""
Configuration Module
====================
Loads environment variables from .env file and provides
centralized access to all application settings.

Handles edge cases:
- EC-0.1: Missing .env file
- EC-0.2: Invalid or expired API key (validation at load time)
- EC-0.5: Incompatible Python version
"""

import os
import sys
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Python version check (EC-0.5)
# ---------------------------------------------------------------------------
MINIMUM_PYTHON = (3, 10)
if sys.version_info < MINIMUM_PYTHON:
    sys.exit(
        f"Error: Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]}+ is required. "
        f"You are using Python {sys.version_info.major}.{sys.version_info.minor}."
    )

# ---------------------------------------------------------------------------
# Load .env file (EC-0.1)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
except ImportError:
    sys.exit(
        "Error: Required packages not installed.\n"
        "Run: pip install -r requirements.txt"
    )

# Resolve project root (three levels up from src/phase0/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

if not ENV_PATH.exists():
    print(
        f"Warning: No .env file found at {ENV_PATH}\n"
        f"Copy .env.example to .env and fill in your settings:\n"
        f"  cp .env.example .env"
    )
    # Still try to load from environment variables
    load_dotenv()
else:
    load_dotenv(ENV_PATH)

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("config")

# ---------------------------------------------------------------------------
# Application Settings
# ---------------------------------------------------------------------------
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

# ---------------------------------------------------------------------------
# LLM Provider Settings
# ---------------------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Ollama (local)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# ---------------------------------------------------------------------------
# Dataset Settings
# ---------------------------------------------------------------------------
DATASET_NAME = os.getenv("DATASET_NAME", "ManikaSaini/zomato-restaurant-recommendation")
DATASET_CACHE_DIR = PROJECT_ROOT / os.getenv("DATASET_CACHE_DIR", "data/")
DATASET_MAX_ROWS = int(os.getenv("DATASET_MAX_ROWS", 100000))

# ---------------------------------------------------------------------------
# Recommendation Settings
# ---------------------------------------------------------------------------
MAX_RECOMMENDATIONS = int(os.getenv("MAX_RECOMMENDATIONS", 5))
MAX_FILTERED_RESULTS = int(os.getenv("MAX_FILTERED_RESULTS", 20))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", 30))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
TEMPLATES_DIR = SRC_DIR / "phase0" / "templates"
STATIC_DIR = SRC_DIR / "phase0" / "static"


def validate_config():
    """Validate critical configuration values at startup."""
    warnings = []

    # Check LLM API key based on selected provider (EC-0.2)
    if LLM_PROVIDER == "openai" and (not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here"):
        warnings.append("OpenAI API key is not configured. LLM features will not work.")
    elif LLM_PROVIDER == "gemini" and (not GEMINI_API_KEY or GEMINI_API_KEY == "your-gemini-api-key-here"):
        warnings.append("Gemini API key is not configured. LLM features will not work.")
    elif LLM_PROVIDER == "groq" and (not GROQ_API_KEY or GROQ_API_KEY == "your-groq-api-key-here"):
        warnings.append("Groq API key is not configured. LLM features will not work.")

    # Check data directory exists
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created data directory: {DATA_DIR}")

    for warning in warnings:
        logger.warning(warning)

    return len(warnings) == 0


def get_config_summary():
    """Return a summary of current configuration for debugging."""
    return {
        "project_root": str(PROJECT_ROOT),
        "app_host": APP_HOST,
        "app_port": APP_PORT,
        "flask_debug": FLASK_DEBUG,
        "llm_provider": LLM_PROVIDER,
        "dataset_name": DATASET_NAME,
        "dataset_cache_dir": str(DATASET_CACHE_DIR),
        "max_recommendations": MAX_RECOMMENDATIONS,
        "max_filtered_results": MAX_FILTERED_RESULTS,
        "llm_timeout_seconds": LLM_TIMEOUT_SECONDS,
        "log_level": LOG_LEVEL,
        "model_costs": {
            "gemini-1.5-flash": {"input": 0.0, "output": 0.0},
            "llama3": {"input": 0.0, "output": 0.0},
            "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
        }
    }


if __name__ == "__main__":
    # Quick test: print configuration
    validate_config()
    import json
    print(json.dumps(get_config_summary(), indent=2))
