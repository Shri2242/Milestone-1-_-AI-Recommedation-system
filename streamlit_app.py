import os
import sys
from pathlib import Path
import streamlit as st

# Setup paths so imports work correctly when hosted
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Attempt to load secrets from Streamlit if deployed, otherwise fallback to local .env
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from src.phase0.utils import validate_preferences
from src.phase3_recommendation.recommender import get_recommendations

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Zomato AI Recommender",
    page_icon="🍽️",
    layout="centered"
)

# --- CSS OVERRIDES ---
st.markdown(
    """
    <style>
    .stApp header {background-color: transparent;}
    .title {
        text-align: center;
        background: linear-gradient(to right, #e23744, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .card {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="title">Zomato AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Find Your Perfect Meal</p>', unsafe_allow_html=True)

# --- USER INPUT FORM ---
with st.form("preferences_form"):
    col1, col2 = st.columns(2)
    with col1:
        location = st.text_input("Location", placeholder="e.g., Indiranagar, Mumbai")
        budget = st.selectbox("Budget", options=["", "low", "medium", "high"], format_func=lambda x: {"": "Any Budget", "low": "Low (₹0–₹500)", "medium": "Medium (₹500–₹1500)", "high": "High (₹1500+)"}[x])
    with col2:
        cuisine = st.text_input("Cuisine", placeholder="e.g., North Indian, Italian")
        additional = st.text_input("Specific Cravings", placeholder="e.g., Biryani, Romantic date")
        
    rating = st.slider("Minimum Rating", min_value=0.0, max_value=5.0, value=3.5, step=0.5)
    
    submitted = st.form_submit_button("Get AI Recommendations", type="primary")

# --- RECOMMENDATION LOGIC ---
if submitted:
    if not location:
        st.warning("Please enter a location to get started.")
    else:
        raw_prefs = {
            "location": location,
            "budget": budget,
            "cuisine": cuisine,
            "min_rating": rating,
            "additional_prefs": additional,
        }
        
        with st.spinner("Analyzing restaurants with AI..."):
            try:
                prefs = validate_preferences(raw_prefs)
                result = get_recommendations(prefs)
                
                st.divider()
                st.subheader("Top Recommendations")
                
                # --- RENDER RESULTS ---
                if not result.has_results:
                    # Phase 5 empty state semantics
                    if result.source == "no_candidates":
                        st.info("🍽️ **No restaurants match your exact filters.** Try relaxing your location, budget, or rating constraints.")
                    else:
                        st.warning("🤖 **AI skipped recommendations.** The LLM could not justify any picks from the filtered list.")
                else:
                    for r in result.recommendations:
                        st.markdown(f"""
                        <div style="border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem; background-color: rgba(255,255,255,0.05);">
                            <h3 style="margin-top: 0; color: #e23744;">#{r.rank} {r.name}</h3>
                            <div style="display: flex; gap: 15px; margin-bottom: 10px; font-size: 0.9rem;">
                                <span>⭐ <b>{r.rating}</b></span>
                                <span>💵 ₹{r.cost_for_two} for two</span>
                                <span>🍽️ {r.cuisine}</span>
                            </div>
                            <p style="margin-bottom: 0; font-size: 0.95rem;"><b>AI Insight:</b> {r.explanation}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with st.expander("Show AI Telemetry & Debug Info"):
                        st.json({
                            "Provider": result.llm_provider,
                            "Model": result.llm_model,
                            "Latency (ms)": result.latency_ms,
                            "Total Candidates Matched": result.filter_result.total_matches,
                            "Source": result.source
                        })
            except Exception as e:
                st.error(f"An error occurred while generating recommendations: {str(e)}")
