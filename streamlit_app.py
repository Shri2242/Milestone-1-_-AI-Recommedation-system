
"""
Phase 8 — Streamlit Deployment
================================
Single-process Python app exposing the recommendation flow via Streamlit.
Complements Phase 7 (Next.js) as a lightweight demo/preview surface.

UX:
- Clean dark-themed form (selectbox, text_input, slider)
- Loading spinner while model runs
- Results with rank, name, cuisine, rating, cost, AI explanation
- Distinct empty states ("no filter match" vs "LLM couldn't justify")
"""

import os
import sys
import time
from pathlib import Path
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Streamlit secrets fallback for deployed env
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

from src.phase0.utils import validate_preferences
from src.phase3_recommendation.recommender import get_recommendations

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="Zomato AI Recommender",
    page_icon="🍽️",
    layout="centered",
)

# ── FONTS ──
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@400;500&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# ── CUSTOM CSS ──
st.markdown(
    """
<style>
    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    }
    .stApp header {background-color: transparent !important;}
    h1, h2, h3, h4, h5, h6 { font-family: 'Outfit', sans-serif; }

    .main-title {
        text-align: center;
        background: linear-gradient(to right, #6366f1, #a855f7, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0;
        padding-top: 1rem;
        letter-spacing: -0.02em;
    }
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.25rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    .rec-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .rec-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99,102,241,0.15);
    }
    .rank-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: white;
        font-weight: 700;
        font-size: 0.85rem;
        margin-right: 10px;
        font-family: 'Outfit', sans-serif;
    }
    .rec-name {
        color: #f1f5f9;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
        font-family: 'Outfit', sans-serif;
    }
    .rec-meta {
        display: flex;
        gap: 16px;
        font-size: 0.85rem;
        color: #cbd5e1;
        margin: 8px 0 10px 0;
    }
    .rec-meta span { display: inline-flex; align-items: center; gap: 4px; }
    .rec-rating { color: #fbbf24; }
    .rec-cost { color: #34d399; }
    .rec-cuisine { color: #94a3b8; }
    .rec-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.08);
        margin: 10px 0;
    }
    .rec-insight {
        color: #94a3b8;
        font-style: italic;
        font-size: 0.85rem;
        margin: 0;
        line-height: 1.5;
    }
    .rec-insight strong { color: #a78bfa; font-style: normal; }
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .ai-badge.green {
        background: rgba(52,211,153,0.15);
        color: #34d399;
        border: 1px solid rgba(52,211,153,0.3);
    }
    .ai-badge.amber {
        background: rgba(251,191,36,0.15);
        color: #fbbf24;
        border: 1px solid rgba(251,191,36,0.3);
    }
    .chip {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 999px;
        background: rgba(99,102,241,0.12);
        border: 1px solid rgba(99,102,241,0.25);
        color: #a5b4fc;
        font-size: 0.78rem;
        margin-right: 6px;
        margin-bottom: 6px;
        font-family: 'Inter', sans-serif;
    }
    .chip-label { color: #818cf8; font-weight: 600; }
    .empty-state {
        text-align: center;
        padding: 2rem 1rem;
    }
    .empty-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
    .empty-headline { color: #94a3b8; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; }
    .empty-subtext { color: #64748b; font-size: 0.9rem; }
    footer { visibility: hidden; }

    /* Override Streamlit defaults for cleaner look */
    .stTextInput>div>div>input, .stSelectbox>div>div>select {
        background-color: rgba(30, 41, 59, 0.7) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif;
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }
    .stSlider>div>div>div {
        color: #f1f5f9 !important;
    }
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #6366f1, #a855f7) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-family: 'Inter', sans-serif;
        transition: opacity 0.2s;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        opacity: 0.9;
    }
    div[data-testid="stFormSubmitButton"] button:disabled {
        opacity: 0.6;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── HEADER ──
st.markdown('<h1 class="main-title">🍽 Zomato AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Discover your next favorite meal, powered by AI.</p>', unsafe_allow_html=True)

# ── FORM ──
with st.form("preferences_form"):
    col1, col2 = st.columns(2)
    with col1:
        location = st.text_input("📍 Location", placeholder="e.g. Indiranagar, Bellandur")
        budget = st.selectbox(
            "💰 Budget",
            options=["", "low", "medium", "high"],
            format_func=lambda x: {
                "": "Any Budget",
                "low": "Low (₹0–₹500)",
                "medium": "Medium (₹500–₹1500)",
                "high": "High (₹1500+)",
            }[x],
        )
    with col2:
        cuisine = st.text_input("🍛 Cuisine", placeholder="e.g. Italian, North Indian")
        additional = st.text_input("✨ Specific Cravings", placeholder="e.g. Biryani, romantic date")

    rating = st.slider(
        "⭐ Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=3.5,
        step=0.5,
    )

    submitted = st.form_submit_button("Get AI Recommendations", use_container_width=True)

# ── RECOMMENDATION LOGIC ──
if submitted:
    if not location.strip():
        st.warning("Please enter a location to get started.")
        st.stop()

    raw_prefs = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine,
        "min_rating": rating,
        "additional_prefs": additional,
    }

    with st.spinner("🍽️ Analyzing restaurants with AI..."):
        try:
            prefs = validate_preferences(raw_prefs)

            start = time.time()
            result = get_recommendations(prefs)
            elapsed_ms = int((time.time() - start) * 1000)

            st.divider()
            st.markdown("### 📊 Top Recommendations")

            # ── FILTER CHIPS ──
            chips = []
            if prefs.get("location"):
                chips.append(f'<span class="chip"><span class="chip-label">Loc:</span> {prefs["location"]}</span>')
            if prefs.get("budget"):
                chips.append(f'<span class="chip"><span class="chip-label">Budget:</span> {prefs["budget"].capitalize()}</span>')
            if prefs.get("cuisine"):
                chips.append(f'<span class="chip"><span class="chip-label">Cuisine:</span> {prefs["cuisine"]}</span>')
            if prefs.get("min_rating", 0) > 0:
                chips.append(f'<span class="chip"><span class="chip-label">Rating:</span> {prefs["min_rating"]}+</span>')
            if chips:
                st.markdown(f'<div style="margin-bottom: 0.75rem;">{"".join(chips)}</div>', unsafe_allow_html=True)

            # ── AI BADGE ──
            if result.source == "llm":
                model_str = result.llm_model or "unknown"
                st.markdown(f'<div class="ai-badge green">✨ Powered by {result.llm_provider} ({model_str}) — {result.latency_ms or elapsed_ms}ms</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="ai-badge amber">⚙ Rule-based Ranking (AI Unavailable)</div>', unsafe_allow_html=True)

            # ── RESULTS / EMPTY STATES ──
            if not result.has_results:
                if result.source == "no_candidates" or (result.filter_result and not result.filter_result.has_results):
                    st.markdown(
                        '<div class="empty-state">'
                        '<div class="empty-icon">🍽️</div>'
                        '<div class="empty-headline">No restaurants match your filters.</div>'
                        '<div class="empty-subtext">Try relaxing your location, budget, or rating constraints.</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="empty-state">'
                        '<div class="empty-icon">🧠</div>'
                        '<div class="empty-headline">The AI couldn\'t justify any picks.</div>'
                        '<div class="empty-subtext">Your filtered options didn\'t meet the model\'s confidence threshold. Try different preferences.</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
            else:
                for r in result.recommendations:
                    st.markdown(
                        f"""
                        <div class="rec-card">
                            <div style="display: flex; align-items: center;">
                                <span class="rank-badge">#{r.rank}</span>
                                <span class="rec-name">{r.name}</span>
                            </div>
                            <div class="rec-meta">
                                <span class="rec-rating">⭐ {r.rating}</span>
                                <span class="rec-cost">₹{r.cost_for_two} for two</span>
                                <span class="rec-cuisine">🍛 {r.cuisine}</span>
                            </div>
                            <hr class="rec-divider" />
                            <p class="rec-insight"><strong>AI Insight:</strong> {r.explanation}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
