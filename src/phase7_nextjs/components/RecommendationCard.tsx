import { RecommendationItem } from "@/types/api";
import styles from "./RecommendationCard.module.css";

interface Props {
  rec: RecommendationItem;
  isAiPowered: boolean;
}

export default function RecommendationCard({ rec, isAiPowered }: Props) {
  const stars = Math.round(rec.rating * 2) / 2;
  const starDisplay = "★".repeat(Math.floor(stars)) + (stars % 1 ? "½" : "");

  return (
    <article className={styles.card}>
      <div className={styles.header}>
        <span className={styles.rank}>#{rec.rank}</span>
        <h2 className={styles.name}>{rec.name}</h2>
      </div>

      <div className={styles.meta}>
        <span className={styles.rating} title={`${rec.rating}/5`}>
          {starDisplay} {rec.rating}
        </span>
        <span className={styles.cost}>₹{rec.cost_for_two} for two</span>
      </div>

      <p className={styles.cuisine}>{rec.cuisine}</p>

      <div className={styles.explanation}>
        <strong>{isAiPowered ? "AI Insight" : "Why we recommend this"}</strong>
        <p>{rec.explanation}</p>
      </div>
    </article>
  );
}
