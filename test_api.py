import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from fastapi.testclient import TestClient
from src.phase6_api.api import app

client = TestClient(app)

print("Testing GET /health")
r_health = client.get("/health")
print(r_health.json())

print("\nTesting POST /api/v1/recommendations")
payload = {
    "location": "Bellandur",
    "budget": "high",
    "cuisine": "",
    "min_rating": 4.0,
    "additional_prefs": "Top 3 restaurants"
}
r_rec = client.post("/api/v1/recommendations", json=payload)
print(f"Status: {r_rec.status_code}")
data = r_rec.json()
print(f"Source: {data.get('source')}")
print(f"Counts: {data.get('counts')}")
print("Recommendations:")
for rec in data.get("recommendations", []):
    print(f"- #{rec.get('rank')} {rec.get('name')} (Cost: {rec.get('cost_for_two')})")
