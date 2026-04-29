"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { RecommendationResponse, Preferences } from "@/types/api";
import RecommendationCard from "@/components/RecommendationCard";
import AIBadge from "@/components/AIBadge";
import EmptyState from "@/components/EmptyState";
import styles from "./results.module.css";

export default function ResultsPage() {
  const router = useRouter();
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const raw = sessionStorage.getItem("recommendations");
    const rawPrefs = sessionStorage.getItem("preferences");
    if (!raw) {
      router.replace("/");
      return;
    }
    setData(JSON.parse(raw));
    if (rawPrefs) setPrefs(JSON.parse(rawPrefs));
  }, [router]);

  if (!data) return null;

  const isAI = data.source === "llm";
  const hasResults = data.recommendations.length > 0;
  const emptyType =
    data.source === "no_candidates" ? "no_match" : "llm_rejected";

  return (
    <main className={`${styles.main} ${darkMode ? styles.dark : styles.light}`}>
      <div className={styles.glowTop} />

      <div className={styles.wrapper}>
        {/* Header */}
        <header className={styles.header}>
          <div className={styles.headerTop}>
            <button className={styles.backBtnTop} onClick={() => router.push("/")}>← Back</button>
            <h1 className={styles.title}>Top Recommendations</h1>
            <button
              className={styles.themeToggle}
              onClick={() => setDarkMode(!darkMode)}
            >
              {darkMode ? "☀️ Day" : "🌙 Night"}
            </button>
          </div>
        </header>

        {/* Filter summary chips */}
        {prefs && (
          <div className={styles.chips}>
            {prefs.location && (
              <span className={styles.chip}>
                <span className={styles.chipLabel}>Loc:</span> {prefs.location}
              </span>
            )}
            {prefs.budget && (
              <span className={styles.chip}>
                <span className={styles.chipLabel}>Budget:</span>{" "}
                {prefs.budget.charAt(0).toUpperCase() + prefs.budget.slice(1)}
              </span>
            )}
            {prefs.cuisine && (
              <span className={styles.chip}>
                <span className={styles.chipLabel}>Cuisine:</span> {prefs.cuisine}
              </span>
            )}
            {prefs.min_rating > 0 && (
              <span className={styles.chip}>
                <span className={styles.chipLabel}>Rating:</span> {prefs.min_rating}+
              </span>
            )}
          </div>
        )}

        {/* AI / fallback badge */}
        {hasResults && (
          <AIBadge
            source={data.source}
            provider={data.telemetry?.provider}
            model={data.telemetry?.model}
            latencyMs={data.telemetry?.latency_ms}
          />
        )}

        {/* Results or empty state */}
        {hasResults ? (
          <div className={styles.grid}>
            {data.recommendations.map((rec) => (
              <RecommendationCard key={rec.id} rec={rec} isAiPowered={isAI} />
            ))}
          </div>
        ) : (
          <EmptyState
            type={emptyType}
            onReset={() => router.push("/")}
          />
        )}

        {/* Footer action */}
        {hasResults && (
          <div className={styles.footer}>
            <button className={styles.backBtn} onClick={() => router.push("/")}>
              ← Modify Search
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
