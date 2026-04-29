import styles from "./EmptyState.module.css";

interface Props {
  type: "no_match" | "llm_rejected";
  onReset: () => void;
}

export default function EmptyState({ type, onReset }: Props) {
  const isNoMatch = type === "no_match";

  return (
    <div className={`${styles.container} ${isNoMatch ? styles.gray : styles.amber}`}>
      <div className={styles.icon}>{isNoMatch ? "🍽" : "🤖"}</div>
      <h2 className={styles.title}>
        {isNoMatch
          ? "No restaurants match your filters."
          : "The AI couldn't justify any picks."}
      </h2>
      <p className={styles.subtitle}>
        {isNoMatch
          ? "Try relaxing your location, budget, or rating constraints."
          : "Your filtered options didn't meet the model's confidence threshold. Try different preferences."}
      </p>
      <button className={styles.btn} onClick={onReset}>
        {isNoMatch ? "Modify Search" : "Try Again"}
      </button>
    </div>
  );
}
