# Google Stitch UI Prompt — AI Restaurant Recommender (Phase 7 Frontend)

> Copy the prompt below and paste it into [Google Stitch](https://stitch.withgoogle.com) to generate UI screens for the Phase 7 frontend. The actual implementation will be in **Next.js (App Router)**.

---

## Stitch Prompt

```
Design a premium, dark-themed web application called "AI Restaurant Recommender" — a Zomato-inspired AI-powered tool that helps users discover top restaurants based on their preferences.

The app has two primary screens:

---

**SCREEN 1: Preference Input Form**

Layout:
- Centered glass-morphism card on a deep dark background (similar to #0f172a to #1e1b4b gradient).
- App title at the top with a vivid gradient text effect (indigo → purple → sky blue).
- Subtitle: "Discover your next favorite meal, powered by AI."

Form elements inside the card:
1. Location text input — placeholder: "e.g. Indiranagar, Bellandur"
2. Two-column row:
   - Budget dropdown — options: Any Budget, Low (₹0–₹500), Medium (₹500–₹1500), High (₹1500+)
   - Cuisine text input — placeholder: "e.g. Italian, North Indian"
3. Minimum Rating slider (0 to 5, step 0.5) with a badge showing selected value
4. Additional Preferences textarea — placeholder: "e.g. must have outdoor seating, romantic spot"
5. Primary CTA button at the bottom: "Get AI Recommendations" with a gradient background (indigo to purple), with a subtle loading spinner state shown when the API call is pending

Design notes:
- Card uses frosted glass effect (backdrop blur, semi-transparent background)
- Soft glow/gradient orbs in the background
- Inputs have dark translucent backgrounds with a subtle glow border on focus
- The rating slider thumb is a glowing indigo circle
- All elements are rounded with generous padding

---

**SCREEN 2: Recommendation Results**

Layout:
- Same dark gradient background
- Smaller header area with app title and "Top Recommendations" label
- A compact filter summary row showing applied filters as pill/chip tags (e.g. "Loc: Bellandur", "Budget: High", "Rating: 4.0+")
- An AI status badge below the chips:
  - Green pill when AI-powered: "✨ Powered by Groq AI (llama-3.3-70b-versatile) — 1.6s"
  - Amber pill when rule-based fallback: "⚙ Rule-based Ranking (AI Unavailable)"
- A responsive grid of recommendation cards (2–3 per row on desktop, 1 per row on mobile)

Each recommendation card:
- Dark translucent card with a subtle glass border
- Top-left: gradient rank badge (e.g. "#1" in a circular indigo-to-purple gradient)
- Restaurant name as the card headline
- Metadata row: star rating (gold), cost (green), cuisine tags (muted)
- A divider line
- "AI Insight:" section with italic explanation text in a lighter muted color
- Hover state: card lifts up with a soft shadow glow

At the bottom:
- "← Modify Search" secondary button (ghost/outline style)

---

**EMPTY STATES (show both variants as separate sub-screens)**

Empty State 1 — No filter match:
- Sad bowl icon or restaurant icon in gray
- Headline: "No restaurants match your filters."
- Subtext: "Try relaxing your location, budget, or rating constraints."
- "Modify Search" button

Empty State 2 — LLM could not justify picks:
- Brain/AI icon in amber
- Headline: "The AI couldn't justify any picks."
- Subtext: "Your filtered options didn't meet the model's confidence threshold. Try different preferences."
- "Try Again" button

---

**Design System:**
- Font: Outfit (headings, 800 weight for titles) + Inter (body, 400/500)
- Primary: Indigo (#6366f1), Secondary: Purple (#a855f7), Accent: Sky Blue (#38bdf8)
- Background: #0f172a → #1e1b4b (135deg gradient)
- Surface: rgba(30, 41, 59, 0.7) with 16px backdrop blur
- Success: #34d399, Warning: #fb923c, Rating: #fbbf24
- Border: rgba(255, 255, 255, 0.1)
- All cards and inputs use border-radius: 16px
- Micro-animations: fade-in on cards, hover lift, button press scale

---

**Implementation context:**
- This is a Next.js 14 (App Router) frontend application.
- Data comes from a Python FastAPI backend running at http://localhost:8000.
- The preference form submits to POST /api/v1/recommendations.
- Show loading state while API call is in flight.
- Mobile-first responsive design.
- No static images required — use CSS-only backgrounds and SVG icons.
```

---

## Screens to Request in Stitch

When Stitch asks which screens to generate, request:

1. **Input Form** — dark, glassmorphic preference form
2. **Results Grid** — AI-powered recommendation cards
3. **Results Grid (Fallback)** — same layout with amber "Rule-based" badge
4. **Empty State: No Match** — gray/muted no results
5. **Empty State: AI Could Not Justify** — amber AI warning state

---

## Notes for Next.js Implementation

Once Stitch generates the UI:
- The implementation will live in `src/phase7_frontend/` as a **Next.js 14 App Router** project.
- Pages map to: `app/page.tsx` (form) and `app/results/page.tsx` (results).
- Components: `RecommendationCard`, `FilterChips`, `EmptyState`, `AIBadge`, `RatingSlider`.
- API call: `fetch("http://localhost:8000/api/v1/recommendations", { method: "POST", body: JSON.stringify(prefs) })`.
- The JSON response shape from the backend is:
```json
{
  "recommendations": [
    { "rank": 1, "name": "...", "cuisine": "...", "rating": 4.6, "cost_for_two": 1800, "explanation": "..." }
  ],
  "source": "llm",
  "counts": { "returned": 5, "candidates": 6 },
  "telemetry": { "latency_ms": 1646, "provider": "groq", "model": "llama-3.3-70b-versatile", "total_candidates": 6, "relaxed_filters": [] },
  "messages": []
}
```
