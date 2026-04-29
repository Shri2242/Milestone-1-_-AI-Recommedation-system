"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { fetchRecommendations } from "@/lib/api";
import { Preferences } from "@/types/api";
import styles from "./page.module.css";

const QUICK_TAGS = ["Italian", "Spicy", "Dessert", "Near Me", "North Indian", "BBQ"];

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rating, setRating] = useState(3.5);
  const [darkMode, setDarkMode] = useState(true);
  const [cuisine, setCuisine] = useState("");
  const [query, setQuery] = useState("");

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const form = e.currentTarget;
    const data = new FormData(form);

    const prefs: Preferences = {
      location: data.get("location") as string,
      budget: data.get("budget") as string,
      cuisine: cuisine,
      min_rating: rating,
      additional_prefs: query || (data.get("additional_prefs") as string),
    };

    try {
      const result = await fetchRecommendations(prefs);
      sessionStorage.setItem("recommendations", JSON.stringify(result));
      sessionStorage.setItem("preferences", JSON.stringify(prefs));
      router.push("/results");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(`Could not connect to the API. Is the backend running?\n${msg}`);
      setLoading(false);
    }
  }

  const theme = darkMode ? styles.dark : styles.light;

  return (
    <div className={`${styles.pageRoot} ${theme}`}>
      {/* Navbar */}
      <nav className={styles.navbar}>
        <div className={styles.navBrand}>
          <span className={styles.logo}>🍽</span>
          <span className={styles.brandName}>Zomato AI</span>
        </div>
        <div className={styles.navLinks}>
          <a href="#" className={`${styles.navLink} ${styles.active}`}>Home</a>
          <a href="#" className={styles.navLink}>Dining Out</a>
          <a href="#" className={styles.navLink}>Delivery</a>
          <a href="#" className={styles.navLink}>Profile</a>
        </div>
        {/* Day/Night toggle */}
        <button
          className={styles.themeToggle}
          onClick={() => setDarkMode(!darkMode)}
          aria-label="Toggle theme"
          title={darkMode ? "Switch to Day Mode" : "Switch to Night Mode"}
        >
          {darkMode ? "☀️ Day" : "🌙 Night"}
        </button>
      </nav>

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroOverlay} />
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>Find Your Perfect Meal with Zomato AI</h1>

          {/* Search bar */}
          <div className={styles.searchBar}>
            <span className={styles.searchIcon}>🎤</span>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Hi! What are you craving today?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              className={styles.searchSendBtn}
              onClick={() => {}}
            >
              Send
            </button>
          </div>

          {/* Quick Tags */}
          <div className={styles.quickTags}>
            {QUICK_TAGS.map((tag) => (
              <button
                key={tag}
                className={`${styles.tag} ${cuisine === tag ? styles.tagActive : ""}`}
                onClick={() => setCuisine(cuisine === tag ? "" : tag)}
                type="button"
              >
                {tag}
              </button>
            ))}
          </div>

          {/* Form card */}
          <form onSubmit={handleSubmit} className={styles.formCard}>
            {error && <div className={styles.errorBox}>{error}</div>}

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="location">Location</label>
                <input
                  id="location"
                  name="location"
                  type="text"
                  placeholder="e.g., Mumbai"
                  required
                  className={styles.input}
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="cuisine-input">Cuisine</label>
                <input
                  id="cuisine-input"
                  type="text"
                  placeholder="e.g., North Indian"
                  value={cuisine}
                  onChange={(e) => setCuisine(e.target.value)}
                  className={styles.input}
                />
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label htmlFor="budget">Budget</label>
                <select id="budget" name="budget" className={styles.select}>
                  <option value="">e.g., ₹500–₹1000</option>
                  <option value="low">Low (₹0–₹500)</option>
                  <option value="medium">Medium (₹500–₹1500)</option>
                  <option value="high">High (₹1500+)</option>
                </select>
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="additional_prefs">Specific Cravings</label>
                <input
                  id="additional_prefs"
                  name="additional_prefs"
                  type="text"
                  placeholder="e.g., Biryani, Butter Chicken"
                  className={styles.input}
                />
              </div>
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="min_rating">
                Minimum Rating — <span className={styles.ratingBadge}>{rating} ★</span>
              </label>
              <input
                id="min_rating"
                name="min_rating"
                type="range"
                min={0}
                max={5}
                step={0.5}
                value={rating}
                onChange={(e) => setRating(parseFloat(e.target.value))}
                className={styles.slider}
              />
            </div>

            <button type="submit" disabled={loading} className={styles.submitBtn}>
              {loading ? (
                <>
                  <span className={styles.spinner} />
                  <span>Finding restaurants...</span>
                </>
              ) : (
                "Get Recommendations"
              )}
            </button>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerBrand}>
          <span className={styles.logo}>🍽</span>
          <span className={styles.brandName}>Zomato AI</span>
        </div>
        <div className={styles.footerSocial}>
          <span>Follow Us:</span>
          <a href="#">f</a>
          <a href="#">𝕏</a>
          <a href="#">in</a>
          <a href="#">▶</a>
        </div>
      </footer>
    </div>
  );
}
