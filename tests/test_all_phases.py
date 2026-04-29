"""Quick verification that all phases work after restructuring."""

print("--- Test 1: Config ---")
from src.phase0.config import PROJECT_ROOT, DATA_DIR
print(f"Project root: {PROJECT_ROOT}")
print(f"Data dir: {DATA_DIR}")

print("\n--- Test 2: Data Loading ---")
from src.phase1_ingestion.preprocessor import load_processed_data
df = load_processed_data()
print(f"Loaded {len(df)} restaurants")

print("\n--- Test 3: Filtering ---")
from src.phase2_filtering.filter_engine import filter_restaurants
r = filter_restaurants({
    "location": "Indiranagar",
    "budget": "medium",
    "cuisine": "Italian",
    "min_rating": 3.5,
    "additional_prefs": "",
})
print(f"Filtered: {r.total_matches} matches, returned {len(r.restaurants)}")

print("\n--- Test 4: Recommender ---")
from src.phase3_recommendation.recommender import get_recommendations
result = get_recommendations({
    "location": "BTM",
    "budget": "low",
    "cuisine": "Chinese",
    "min_rating": 3.0,
    "additional_prefs": "",
})
print(f"Recommendations: {len(result.recommendations)} ({result.source})")
for rec in result.recommendations:
    print(f"  #{rec.rank} {rec.name} - {rec.rating}/5")

print("\n=== ALL TESTS PASSED! ===")
