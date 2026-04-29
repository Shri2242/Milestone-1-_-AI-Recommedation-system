import styles from "./AIBadge.module.css";

interface Props {
  source: string;
  provider?: string;
  model?: string;
  latencyMs?: number;
}

export default function AIBadge({ source, provider, model, latencyMs }: Props) {
  const isAI = source === "llm";

  return (
    <div className={`${styles.badge} ${isAI ? styles.ai : styles.fallback}`}>
      {isAI ? (
        <>
          <span className={styles.icon}>✨</span>
          <span>
            Powered by AI
            {provider && model && (
              <span className={styles.detail}>
                {" "}({provider.charAt(0).toUpperCase() + provider.slice(1)}: {model}
                {latencyMs ? ` — ${latencyMs}ms` : ""})
              </span>
            )}
          </span>
        </>
      ) : (
        <>
          <span className={styles.icon}>⚙</span>
          <span>Rule-based Ranking (AI Unavailable)</span>
        </>
      )}
    </div>
  );
}
