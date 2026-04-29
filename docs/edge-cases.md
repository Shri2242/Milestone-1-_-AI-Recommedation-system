# Edge Cases — AI-Powered Restaurant Recommendation System

This document catalogs all identified edge cases across the system, organized by phase and component. Each edge case includes **a description, expected behavior, severity, and the phase it belongs to**.

---

## Severity Legend

| Level | Meaning |
|-------|---------|
| 🔴 **Critical** | System crashes or returns completely wrong results |
| 🟠 **High** | Major feature broken or unusable experience |
| 🟡 **Medium** | Degraded experience but system remains functional |
| 🟢 **Low** | Minor cosmetic or UX issue |

---

## Phase 0 — Project Setup & Configuration

### EC-0.1: Missing `.env` File

| Attribute | Detail |
|-----------|--------|
| **Description** | User clones the repo but doesn't create a `.env` file |
| **Expected Behavior** | App should detect missing `.env`, display a clear error message listing required variables, and exit gracefully |
| **Severity** | 🔴 Critical |

### EC-0.2: Invalid or Expired API Key

| Attribute | Detail |
|-----------|--------|
| **Description** | The LLM API key in `.env` is incorrect, expired, or has exceeded its quota |
| **Expected Behavior** | App should catch the authentication error, display a user-friendly message ("Invalid API key — please check your `.env` file"), and not expose raw error traces |
| **Severity** | 🔴 Critical |

### EC-0.3: Port Already in Use

| Attribute | Detail |
|-----------|--------|
| **Description** | The default web server port (e.g., 5000) is already occupied by another application |
| **Expected Behavior** | App should either auto-select an available port or display a clear message asking the user to free the port or configure an alternative |
| **Severity** | 🟡 Medium |

### EC-0.4: Missing Python Dependencies

| Attribute | Detail |
|-----------|--------|
| **Description** | User runs the app without installing required packages |
| **Expected Behavior** | ImportError should be caught at startup with a message: "Run `pip install -r requirements.txt` first" |
| **Severity** | 🔴 Critical |

### EC-0.5: Incompatible Python Version

| Attribute | Detail |
|-----------|--------|
| **Description** | User runs the app with Python < 3.10 |
| **Expected Behavior** | Version check at startup; display minimum version requirement and exit |
| **Severity** | 🟠 High |

---

## Phase 1 — Data Ingestion & Preprocessing

### EC-1.1: Hugging Face API Unavailable / Rate Limited

| Attribute | Detail |
|-----------|--------|
| **Description** | The Hugging Face API is down, rate-limited, or blocked by firewall |
| **Expected Behavior** | Retry with exponential backoff (max 3 retries). If all retries fail, check for a local cached copy of the dataset. If no cache exists, display: "Unable to download dataset. Please check your internet connection." |
| **Severity** | 🔴 Critical |

### EC-1.2: Dataset Schema Change

| Attribute | Detail |
|-----------|--------|
| **Description** | The upstream Hugging Face dataset changes column names or structure |
| **Expected Behavior** | Validate expected columns at load time. If key columns are missing, log a warning and raise a clear error: "Dataset schema has changed. Expected columns: [list]. Found: [list]." |
| **Severity** | 🔴 Critical |

### EC-1.3: Empty Dataset

| Attribute | Detail |
|-----------|--------|
| **Description** | The downloaded dataset has 0 rows |
| **Expected Behavior** | Detect empty dataset after download, log the issue, and display: "Dataset appears to be empty. Please try again later." |
| **Severity** | 🔴 Critical |

### EC-1.4: Missing Values in Critical Fields

| Attribute | Detail |
|-----------|--------|
| **Description** | Rows with null/empty values in `name`, `city`, `cuisines`, or `rating` |
| **Expected Behavior** | Drop rows where `name` is null. For other fields: fill `rating` with 0.0 (and flag as "Unrated"), fill `cuisines` with "Unknown", fill `city` with "Unknown". Log count of rows affected. |
| **Severity** | 🟡 Medium |

### EC-1.5: Duplicate Restaurants

| Attribute | Detail |
|-----------|--------|
| **Description** | Same restaurant appears multiple times (same name + same city) |
| **Expected Behavior** | Deduplicate by keeping the entry with the highest vote count. Log the number of duplicates removed. |
| **Severity** | 🟡 Medium |

### EC-1.6: Corrupt or Malformed Data

| Attribute | Detail |
|-----------|--------|
| **Description** | Non-numeric values in `rating` or `cost` columns, or strings with special characters |
| **Expected Behavior** | Coerce to numeric types with `errors='coerce'`. Resulting NaNs handled per EC-1.4 rules. |
| **Severity** | 🟠 High |

### EC-1.7: Extremely Large Dataset

| Attribute | Detail |
|-----------|--------|
| **Description** | Dataset is unexpectedly large (>1 GB), causing memory issues |
| **Expected Behavior** | Use chunked loading or streaming. Set a configurable row limit (default: 100,000). Log a warning if the limit is hit. |
| **Severity** | 🟡 Medium |

### EC-1.8: Disk Space Insufficient

| Attribute | Detail |
|-----------|--------|
| **Description** | Not enough disk space to save the processed dataset |
| **Expected Behavior** | Check available disk space before writing. Display: "Insufficient disk space. Need at least X MB." |
| **Severity** | 🟠 High |

---

## Phase 2 — Filtering & Matching Engine

### EC-2.1: No Restaurants Match All Criteria

| Attribute | Detail |
|-----------|--------|
| **Description** | User's combination of preferences (e.g., "Italian in Jaipur, under ₹200, 4.5+ rating") matches zero restaurants |
| **Expected Behavior** | Progressively relax filters in order: rating → budget → cuisine. Show results with a message: "No exact matches found. Here are the closest options (relaxed: rating)." |
| **Severity** | 🟠 High |

### EC-2.2: Misspelled Location

| Attribute | Detail |
|-----------|--------|
| **Description** | User types "Bangalor" instead of "Bangalore" or "Dlehi" instead of "Delhi" |
| **Expected Behavior** | Fuzzy match with a similarity threshold (≥80%). If match found, auto-correct and show: "Showing results for **Bangalore** (did you mean this?)". If no match, show: "Location not found. Available locations: [list top 10]." |
| **Severity** | 🟠 High |

### EC-2.3: Misspelled Cuisine

| Attribute | Detail |
|-----------|--------|
| **Description** | User types "Itlian" or "Chineese" |
| **Expected Behavior** | Same fuzzy matching strategy as EC-2.2. Auto-correct and display suggestion. |
| **Severity** | 🟠 High |

### EC-2.4: Location Not in Dataset

| Attribute | Detail |
|-----------|--------|
| **Description** | User enters a valid city that doesn't exist in the Zomato dataset (e.g., "Shimla") |
| **Expected Behavior** | Display: "Sorry, we don't have restaurant data for **Shimla** yet. Try one of: Delhi, Mumbai, Bangalore, ..." |
| **Severity** | 🟡 Medium |

### EC-2.5: Multiple Cuisines Selected

| Attribute | Detail |
|-----------|--------|
| **Description** | User wants "Italian AND Chinese" restaurants |
| **Expected Behavior** | Support OR-based filtering (restaurants serving Italian **or** Chinese). If user explicitly wants AND, filter for restaurants serving both. Clarify with a toggle: "Any of these / All of these". |
| **Severity** | 🟡 Medium |

### EC-2.6: Budget Boundary Values

| Attribute | Detail |
|-----------|--------|
| **Description** | Restaurant costs exactly ₹500 (boundary between Low and Medium) |
| **Expected Behavior** | Include boundary values in both adjacent ranges (₹500 appears in both Low and Medium). Document this overlap behavior. |
| **Severity** | 🟢 Low |

### EC-2.7: Minimum Rating of 5.0

| Attribute | Detail |
|-----------|--------|
| **Description** | User sets minimum rating to the maximum possible (5.0) |
| **Expected Behavior** | Very few or no results expected. Apply progressive relaxation per EC-2.1 with a message: "Very few restaurants have a perfect 5.0 rating. Showing top-rated options instead." |
| **Severity** | 🟡 Medium |

### EC-2.8: All Fields Left Empty / Default

| Attribute | Detail |
|-----------|--------|
| **Description** | User clicks "Get Recommendations" without filling any preferences |
| **Expected Behavior** | Either require at least one field (show validation error) or return the top-rated restaurants globally with a message: "Showing top restaurants across all locations." |
| **Severity** | 🟡 Medium |

### EC-2.9: Special Characters in Input

| Attribute | Detail |
|-----------|--------|
| **Description** | User enters `<script>alert('xss')</script>` or SQL injection patterns |
| **Expected Behavior** | Sanitize all inputs. Strip HTML tags and special characters. No raw user input should reach the database or LLM prompt without sanitization. |
| **Severity** | 🔴 Critical |

### EC-2.10: Very Large Number of Filtered Results

| Attribute | Detail |
|-----------|--------|
| **Description** | Broad filters (e.g., "Any cuisine in Delhi, any budget") return 5,000+ results |
| **Expected Behavior** | Cap results sent to LLM at top 20 (sorted by rating × votes). Display: "Found 5,234 restaurants. Showing the top recommendations." |
| **Severity** | 🟡 Medium |

---

## Phase 3 — LLM Integration & Recommendation Engine

### EC-3.1: LLM API Timeout

| Attribute | Detail |
|-----------|--------|
| **Description** | LLM API takes longer than the configured timeout (e.g., >30 seconds) |
| **Expected Behavior** | Cancel the request after timeout. Fall back to rule-based ranking (sort by rating, then votes). Display: "AI recommendations are taking too long. Here are our top picks based on ratings." |
| **Severity** | 🟠 High |

### EC-3.2: LLM Returns Invalid JSON

| Attribute | Detail |
|-----------|--------|
| **Description** | LLM response is not valid JSON or doesn't match the expected schema |
| **Expected Behavior** | Attempt to extract partial data using regex/heuristics. If parsing fails completely, retry once with a stricter prompt. If still failing, fall back to rule-based ranking. Log the malformed response for debugging. |
| **Severity** | 🟠 High |

### EC-3.3: LLM Hallucinates Restaurant Names

| Attribute | Detail |
|-----------|--------|
| **Description** | LLM invents restaurant names that don't exist in the filtered dataset |
| **Expected Behavior** | Cross-validate LLM output against the filtered dataset. Only include restaurants that exist in the data. Strip out any hallucinated entries and log them. |
| **Severity** | 🔴 Critical |

### EC-3.4: LLM Returns Fewer Than Requested Recommendations

| Attribute | Detail |
|-----------|--------|
| **Description** | Asked for top 5 but LLM only returns 2–3 |
| **Expected Behavior** | Accept partial results. Supplement with rule-based picks to fill remaining slots. Display: "AI recommended 3 restaurants. Additional picks based on ratings are included." |
| **Severity** | 🟡 Medium |

### EC-3.5: LLM Rate Limit Exceeded

| Attribute | Detail |
|-----------|--------|
| **Description** | Too many API calls in a short period hit the provider's rate limit |
| **Expected Behavior** | Implement request queuing with exponential backoff. For concurrent users, add a simple in-memory cache (same preferences → same results for 5 minutes). Display: "High demand. Please try again in a moment." |
| **Severity** | 🟠 High |

### EC-3.6: Prompt Token Limit Exceeded

| Attribute | Detail |
|-----------|--------|
| **Description** | Filtered data + prompt exceed the model's context window (e.g., 4K/8K tokens) |
| **Expected Behavior** | Truncate restaurant data to fit within token limits. Prioritize higher-rated restaurants. Log a warning: "Trimmed input to fit token limit. Some lower-rated options were excluded." |
| **Severity** | 🟠 High |

### EC-3.7: LLM Provider Switching

| Attribute | Detail |
|-----------|--------|
| **Description** | Primary LLM provider (e.g., OpenAI) is down; need to switch to backup (e.g., Gemini) |
| **Expected Behavior** | Automatic failover to the next provider in the configured list. Log the switch. No user-facing disruption. |
| **Severity** | 🟡 Medium |

### EC-3.8: Biased or Inappropriate LLM Output

| Attribute | Detail |
|-----------|--------|
| **Description** | LLM generates responses with biased, offensive, or irrelevant content |
| **Expected Behavior** | Apply a basic content filter on LLM output. If flagged, discard the response and fall back to rule-based ranking. Log the incident for review. |
| **Severity** | 🔴 Critical |

### EC-3.9: Cost Tracking for API Calls

| Attribute | Detail |
|-----------|--------|
| **Description** | No visibility into how much each LLM call costs |
| **Expected Behavior** | Log estimated token usage and cost per request. Add a configurable daily spending cap. Alert (log/email) when 80% of the cap is reached. |
| **Severity** | 🟡 Medium |

---

## Phase 4 — UI, Integration & Deployment

### EC-4.1: Slow Page Load on Mobile

| Attribute | Detail |
|-----------|--------|
| **Description** | UI assets are too large or unoptimized for mobile connections |
| **Expected Behavior** | Minify CSS/JS. Use responsive images. Target < 3 second load time on 3G. |
| **Severity** | 🟡 Medium |

### EC-4.2: Form Resubmission on Page Refresh

| Attribute | Detail |
|-----------|--------|
| **Description** | User refreshes the results page, causing the form to resubmit and trigger another LLM call |
| **Expected Behavior** | Use POST-Redirect-GET pattern. After form submission, redirect to a results page with a unique result ID. Refresh loads from cache, not a new LLM call. |
| **Severity** | 🟠 High |

### EC-4.3: Concurrent Users Overwhelm the Server

| Attribute | Detail |
|-----------|--------|
| **Description** | Many users submit preferences simultaneously |
| **Expected Behavior** | Use async request handling. Queue LLM calls. Show position in queue if wait time > 5 seconds. Set a max concurrent request limit. |
| **Severity** | 🟠 High |

### EC-4.4: Browser Back Button Breaks Flow

| Attribute | Detail |
|-----------|--------|
| **Description** | User clicks back from results page and resubmits with stale data |
| **Expected Behavior** | Preserve form state on the input page. Handle gracefully without duplicate submissions. |
| **Severity** | 🟢 Low |

### EC-4.5: Long LLM Wait — No Feedback

| Attribute | Detail |
|-----------|--------|
| **Description** | User stares at a blank screen for 10+ seconds while LLM processes |
| **Expected Behavior** | Show animated loading indicator with contextual messages: "Finding the best restaurants for you...", "Analyzing flavors and ratings...", "Almost there!" |
| **Severity** | 🟠 High |

### EC-4.6: Results Page with No Recommendations

| Attribute | Detail |
|-----------|--------|
| **Description** | Filtering + LLM both return zero usable results |
| **Expected Behavior** | Display a friendly empty state: "We couldn't find matching restaurants. Try broadening your search." with quick-action buttons to modify each filter. |
| **Severity** | 🟡 Medium |

### EC-4.7: Session/State Loss

| Attribute | Detail |
|-----------|--------|
| **Description** | User's session expires mid-interaction or server restarts |
| **Expected Behavior** | Store minimal state client-side (localStorage). If session is lost, redirect to the input page with a message: "Your session expired. Please enter your preferences again." |
| **Severity** | 🟡 Medium |

### EC-4.8: Accessibility (a11y) Issues

| Attribute | Detail |
|-----------|--------|
| **Description** | UI is not usable with screen readers or keyboard-only navigation |
| **Expected Behavior** | Use semantic HTML, ARIA labels, proper focus management. All interactive elements must be keyboard-accessible. Color contrast must meet WCAG AA. |
| **Severity** | 🟡 Medium |

### EC-4.9: Docker Build Fails on Different OS

| Attribute | Detail |
|-----------|--------|
| **Description** | Dockerfile works on Linux but fails on Windows/Mac |
| **Expected Behavior** | Use multi-stage builds with a standard base image (e.g., `python:3.10-slim`). Test on all target platforms. Document OS-specific gotchas in README. |
| **Severity** | 🟡 Medium |

---

## Cross-Cutting Edge Cases

### EC-X.1: Network Disconnection Mid-Request

| Attribute | Detail |
|-----------|--------|
| **Description** | User's internet drops after submitting preferences but before receiving results |
| **Expected Behavior** | Client-side timeout with retry button. Display: "Connection lost. Click to retry." Server-side: abort the LLM call to avoid wasted tokens. |
| **Severity** | 🟠 High |

### EC-X.2: Logging & Monitoring Gaps

| Attribute | Detail |
|-----------|--------|
| **Description** | Errors occur silently with no trace for debugging |
| **Expected Behavior** | Structured logging (JSON format) for all key events: request received, filters applied, LLM called, response parsed, errors encountered. Include request IDs for tracing. |
| **Severity** | 🟡 Medium |

### EC-X.3: Data Privacy — User Input Storage

| Attribute | Detail |
|-----------|--------|
| **Description** | User preferences are logged or stored without consent |
| **Expected Behavior** | Do not persist personally identifiable information. If analytics are needed, anonymize data. Display a brief privacy notice on the input page. |
| **Severity** | 🟠 High |

### EC-X.4: Unicode / Non-English Input

| Attribute | Detail |
|-----------|--------|
| **Description** | User enters preferences in Hindi, Urdu, or other non-Latin scripts |
| **Expected Behavior** | Gracefully handle UTF-8 input. If matching fails, display: "Please enter preferences in English for best results." Do not crash or display garbled text. |
| **Severity** | 🟡 Medium |

---

## Summary by Phase

| Phase | Total Edge Cases | 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low |
|-------|-----------------|-------------|---------|-----------|--------|
| **0** | 5 | 3 | 1 | 1 | 0 |
| **1** | 8 | 3 | 2 | 3 | 0 |
| **2** | 10 | 1 | 3 | 5 | 1 |
| **3** | 9 | 2 | 4 | 3 | 0 |
| **4** | 9 | 0 | 3 | 6 | 0 |
| **Cross-Cutting** | 4 | 0 | 2 | 2 | 0 |
| **Total** | **45** | **9** | **15** | **20** | **1** |
