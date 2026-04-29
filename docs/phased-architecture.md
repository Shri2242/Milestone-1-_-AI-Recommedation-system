# Phased Architecture — AI-Powered Restaurant Recommendation System

This document outlines the **phase-wise implementation plan** for the Zomato-inspired AI restaurant recommendation system. Each phase builds incrementally on the previous one, ensuring a stable, testable deliverable at every stage.

---

## Architecture Overview

```
Phase 0 ──▶ Phase 1 ──▶ Phase 2 ──▶ Phase 3 ──▶ Phase 4
 Setup       Data        Core        LLM         Polish
 & Config    Pipeline    Filtering   Integration  & Deploy
```

---

## Phase 0 — Project Setup & Configuration

**Goal:** Establish the project skeleton, tooling, and a **basic Web UI (Flask) as the sole source of user input**. All user preferences will be collected through the web interface — no CLI or alternative input methods.

### Deliverables

| Item | Description |
|------|-------------|
| Project structure | Organized folder layout (`docs/`, `data/`, `src/`, `tests/`) |
| Environment config | Python virtual environment, `requirements.txt` / `pyproject.toml` |
| Configuration management | `.env` file for API keys, model settings, dataset paths |
| **Basic Web UI (Primary Input Source)** | A Flask web interface that serves as the **only source of user input**. Collects location, budget, cuisine, rating, and additional preferences via a browser-based form. |
| Documentation | Problem statement and architecture docs in `docs/` |

> **Note:** The Web UI is the single entry point for all user interactions from Phase 0 onward. There is no CLI or API-based input mode. All subsequent phases (filtering, LLM, results) will receive user preferences from this Web UI.

### Folder Structure

```
project-root/
├── docs/
│   ├── problemstatement.md
│   ├── phased-architecture.md
│   └── edge-cases.md
├── data/
│   └── (downloaded dataset will go here)
├── src/
│   ├── __init__.py
│   ├── config.py          # Environment & configuration loader
│   ├── app.py             # Web UI entry point
│   └── utils.py           # Shared helper functions
├── tests/
│   └── __init__.py
├── .env.example
├── requirements.txt
└── README.md
```

### Acceptance Criteria

- [ ] Project runs without errors after cloning and installing dependencies
- [ ] Web UI loads and displays a form for user preferences (location, budget, cuisine, rating, additional prefs)
- [ ] Form submission captures and logs user input to the console/terminal
- [ ] All configuration values are loaded from `.env`

---

## Phase 1 — Data Ingestion & Preprocessing

**Goal:** Download, clean, and prepare the Zomato dataset for downstream filtering.

### Deliverables

| Item | Description |
|------|-------------|
| Dataset downloader | Script to fetch the dataset from Hugging Face |
| Data cleaning | Handle missing values, normalize field names, standardize types |
| Data storage | Save processed data as CSV/Parquet for fast local access |
| Data exploration | Summary statistics and sample outputs for validation |

### Key Files

```
src/
├── data_ingestion/
│   ├── __init__.py
│   ├── downloader.py      # Fetch dataset from Hugging Face
│   ├── preprocessor.py    # Clean, normalize, and transform data
│   └── explorer.py        # Generate data summaries and stats
```

### Data Fields to Extract & Normalize

| Field | Raw Source | Normalized Format |
|-------|-----------|-------------------|
| Restaurant Name | `name` | String (trimmed) |
| Location / City | `city` / `location` | Lowercase string |
| Cuisine(s) | `cuisines` | List of strings |
| Cost for Two | `average_cost_for_two` | Integer (INR) |
| Rating | `aggregate_rating` | Float (0.0–5.0) |
| Votes | `votes` | Integer |
| Has Online Delivery | `has_online_delivery` | Boolean |
| Has Table Booking | `has_table_booking` | Boolean |

### Acceptance Criteria

- [ ] Dataset is downloaded and saved to `data/` folder
- [ ] Cleaned dataset has no critical missing values in key fields
- [ ] Data exploration script prints summary stats (row count, unique cities, cuisine distribution)
- [ ] Processed data loads in under 2 seconds

---

## Phase 2 — Filtering & Matching Engine

**Goal:** Build the core logic that filters restaurants based on user preferences.

### Deliverables

| Item | Description |
|------|-------------|
| Filter engine | Multi-criteria filtering (location, budget, cuisine, rating) |
| Budget mapping | Map "Low/Medium/High" labels to cost ranges |
| Fuzzy matching | Handle partial/misspelled cuisine and location names |
| Result preparation | Format filtered results for LLM prompt injection |

### Key Files

```
src/
├── filtering/
│   ├── __init__.py
│   ├── filter_engine.py   # Core filtering logic
│   ├── budget_mapper.py   # Budget label → cost range mapping
│   └── fuzzy_match.py     # Fuzzy string matching for cuisines/locations
```

### Budget Mapping Strategy

| Label | Cost for Two (INR) |
|-------|--------------------|
| Low | ₹0 – ₹500 |
| Medium | ₹500 – ₹1,500 |
| High | ₹1,500+ |

### Filter Pipeline

```
User Input
    │
    ▼
┌─────────────────┐
│ Location Filter  │──▶ Match city/area (fuzzy)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Budget Filter    │──▶ Map label → cost range → filter
└────────┬────────┘
         ▼
┌─────────────────┐
│ Cuisine Filter   │──▶ Match cuisine(s) (fuzzy)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Rating Filter    │──▶ Filter by minimum rating
└────────┬────────┘
         ▼
┌─────────────────┐
│ Additional Prefs │──▶ Online delivery, table booking, etc.
└────────┬────────┘
         ▼
   Filtered Results
   (Top N candidates)
```

### Acceptance Criteria

- [ ] Filtering returns relevant results for valid inputs
- [ ] Fuzzy matching handles minor typos (e.g., "Bangalor" → "Bangalore")
- [ ] Empty result sets are handled gracefully with user-friendly messages
- [ ] Filtered output includes all fields required for the LLM prompt
- [ ] Unit tests cover each filter independently and in combination

---

## Phase 3 — LLM Integration & Recommendation Engine

**Goal:** Integrate an LLM to rank, explain, and personalize restaurant recommendations.

### Deliverables

| Item | Description |
|------|-------------|
| LLM connector | API integration with OpenAI / Gemini / local model |
| Prompt engineering | Structured prompt template for ranking & explanation |
| Response parser | Extract structured recommendations from LLM response |
| Fallback handling | Graceful degradation if LLM is unavailable |

### Key Files

```
src/
├── recommendation/
│   ├── __init__.py
│   ├── llm_connector.py   # LLM API wrapper (supports multiple providers)
│   ├── prompt_builder.py  # Build structured prompts from filtered data
│   ├── response_parser.py # Parse LLM output into structured format
│   └── recommender.py     # Orchestrates the full recommendation flow
```

### Prompt Template (Example)

```
You are an expert restaurant recommendation assistant.

A user is looking for restaurants with these preferences:
- Location: {location}
- Budget: {budget}
- Cuisine: {cuisine}
- Minimum Rating: {min_rating}
- Additional: {additional_prefs}

Here are the matching restaurants from our database:

{filtered_restaurant_data}

Please:
1. Rank the top 5 restaurants based on how well they match the user's preferences.
2. For each restaurant, provide a brief explanation of why it's a good fit.
3. Highlight any standout features (e.g., exceptional rating, great value, unique cuisine).

Respond in the following JSON format:
[
  {
    "rank": 1,
    "name": "...",
    "cuisine": "...",
    "rating": ...,
    "cost_for_two": ...,
    "explanation": "..."
  }
]
```

### LLM Provider Support

| Provider | Model | Notes |
|----------|-------|-------|
| OpenAI | GPT-4 / GPT-3.5 | Primary option |
| Google | Gemini Pro | Alternative |
| Local | Ollama (Llama 3) | Offline / free option |

### Acceptance Criteria

- [ ] LLM generates valid, parseable recommendation responses
- [ ] Recommendations are relevant to user preferences
- [ ] System handles LLM API errors gracefully (timeout, rate limit, invalid response)
- [ ] Fallback to rule-based ranking if LLM is unavailable
- [ ] Response time is under 10 seconds end-to-end

---

## Phase 4 — UI Polish, End-to-End Integration & Deployment

**Goal:** Wire everything together with a polished UI and prepare for deployment.

### Deliverables

| Item | Description |
|------|-------------|
| Full UI | Polished Web UI displaying recommendations with explanations |
| End-to-end flow | User input → filtering → LLM → results displayed on screen |
| Error handling | User-facing error messages for all failure scenarios |
| Loading states | Visual feedback while LLM processes the request |
| Deployment config | Dockerfile / deployment scripts for cloud hosting |

### Key Files

```
src/
├── app.py                 # Updated with full recommendation flow
├── templates/
│   ├── index.html         # Input form (enhanced)
│   └── results.html       # Recommendation display page
├── static/
│   ├── style.css          # Styling
│   └── script.js          # Client-side interactivity
```

### UI Screens

#### Input Screen
- Clean form with dropdowns for location, budget, cuisine
- Slider for minimum rating
- Text field for additional preferences
- "Get Recommendations" button with loading animation

#### Results Screen
- Card-based layout for each recommendation
- Each card shows: rank, name, cuisine, rating, cost, AI explanation
- Option to refine search / start over
- Visual indicators for rating (stars) and budget (₹ symbols)

### End-to-End Flow

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐    ┌──────────────┐
│  Web UI  │───▶│  Capture     │───▶│  Filter      │───▶│  LLM       │───▶│  Display     │
│  (Form)  │    │  User Input  │    │  Engine      │    │  Ranking   │    │  Results     │
└──────────┘    └──────────────┘    └──────────────┘    └────────────┘    └──────────────┘
```

### Acceptance Criteria

- [ ] Full user journey works without errors
- [ ] UI is responsive and works on mobile/desktop
- [ ] Loading indicator shows while waiting for LLM response
- [ ] Error states shown clearly (no restaurants found, LLM error, etc.)
- [ ] Application can be deployed via Docker or a cloud platform
- [ ] README includes setup instructions, usage guide, and screenshots

---

## Phase Summary

| Phase | Name | Key Outcome | Dependencies |
|-------|------|-------------|--------------|
| **0** | Setup & Config | Project skeleton + basic Web UI | None |
| **1** | Data Pipeline | Clean, queryable restaurant dataset | Phase 0 |
| **2** | Filtering Engine | Multi-criteria restaurant filtering | Phase 1 |
| **3** | LLM Integration | AI-powered ranking & explanations | Phase 2 |
| **4** | Polish & Deploy | Production-ready application | Phase 3 |

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10+ |
| **Web Framework** | Flask / Streamlit |
| **Data Processing** | Pandas |
| **Dataset Source** | Hugging Face Datasets |
| **LLM Provider** | OpenAI / Gemini / Ollama |
| **Fuzzy Matching** | FuzzyWuzzy / RapidFuzz |
| **Deployment** | Docker / Railway / Render |
| **Config Management** | python-dotenv |

---

## Phase 5 — Output and experience
**Surface**: Responsibility
**Rendering**: For each recommendation: name, cuisine, rating, estimated cost, AI explanation (per problem statement).
**Empty states**: “No restaurants match filters” vs “LLM could not justify picks”—different copy.
**Observability (light)**: Log latency, token usage if available, and filter counts (no PII in logs unless required).

**Exit criteria**: demo path from user input to readable results in one run; copy and layout match the minimum fields in the problem statement.
**Implemented**: package `src/phase5_output/` (markdown/plain rendering, empty-state copy, stderr telemetry JSON). CLI: `milestone1 recommend-run` (end-to-end readable output + telemetry).

---

## Phase 6 — Backend (HTTP API)
**Concern**: Approach
**Role**: Thin HTTP service that owns server-side secrets (`GROQ_API_KEY`), dataset access, and orchestration. The browser must not call Groq or Hugging Face directly.
**Contract**: Stable JSON request/response for “recommend”: preferences body aligned with Phase 2 keys; response carries ranked items (ids + display fields + explanations), source (llm / fallback / no_candidates), filter/candidate counts, and optional non-sensitive telemetry fields for the UI.
**Endpoints (v1 intent)**: 
- `POST /api/v1/recommendations` (or equivalent) — validate input, run load_restaurants (with limits/caching policy), recommend_with_groq, return DTOs. 
- `GET /health` — process up, keys configured (without exposing values). 
- Optional: `GET /api/v1/meta` — e.g. sample allowed_cities cap for form hints.
**Cross-cutting**: Timeouts aligned with Phase 4; structured server logs (counts, latency, token totals—no raw user notes in info-level logs unless you explicitly choose to); CORS restricted to the dev frontend origin; request size limits on free-text fields (reuse Phase 2 max length).
**Stack**: Python-first is natural: e.g. FastAPI or Flask in `src/` or a sibling package.

**Exit criteria**: frontend can complete one recommendation flow using only the API; API returns the same logical outcomes as recommend-run for the same inputs (modulo caching).

---

## Phase 7 — Frontend (web UI)
**Concern**: Approach
**Role**: Primary user-facing surface: preference form + results list.
**Data flow**: Browser only talks to the Phase 6 API. Map form fields to the API JSON schema (location, budget band, cuisines, minimum rating, optional additional text).
**UI**: Results show name, cuisines, rating, estimated cost, AI explanation for each row; reuse Phase 5 empty-state semantics (“no filter match” vs “model returned no grounded picks”) with clear, distinct copy.
**UX**: Loading states, validation errors inline, disabled submit while pending; optional “copy as Markdown” for demo.
**Stack**: Choose one and stay consistent: e.g. React + Vite (SPA) or HTMX + server templates (minimal JS). Host locally for milestone 1; no production SLA required in Phase 0.

**Exit criteria**: one demo path in the README: start API + UI, submit preferences, see ranked results or an intentional empty state.

---

## Phase 8 — Deployment using Streamlit (optional)
**Concern**: Approach
**Role**: A single-process Python app (Streamlit) that exposes the same recommendation flow as the CLI/API.
**Secrets**: `GROQ_API_KEY` via Streamlit secrets (`st.secrets`) on Streamlit Community Cloud or via environment variables when self-hosting.
**Deployment (free tier)**: Streamlit Community Cloud: connect the GitHub repo, set the main file path, add secrets in the dashboard, deploy.
**Relationship to Phase 6–7**: Complementary: Phase 7 remains the primary product UI (browser + REST). Phase 8 is ideal for course demos, stakeholder previews, and fast sharing. 
**UX scope**: Forms with `st.selectbox` / `st.text_input` / `st.slider` for location, cuisines, budget, minimum rating, and additional text; `st.spinner` while the model runs; `st.expander` for raw JSON or telemetry if useful. Match empty-state copy from Phase 5 where practical.

**Exit criteria**: README (or a short `docs/streamlit-deploy.md`) documents how to run locally (`streamlit run …`) and how to deploy to Community Cloud.

---

## Phase 9 — Hardening and handoff (optional but recommended)
- Automated tests for filters, prompt shape, JSON parsing (fixtures with fake LLM responses), and API contract tests (golden JSON for happy/empty/error paths).
- README: install, set `GROQ_API_KEY`, run API + UI, CLI fallbacks, and limitations.
- Cost/latency notes: candidate cap, model id, when to raise load limits, caching strategy for repeated queries (optional in-process LRU of recent Hub windows—only if measured need).
