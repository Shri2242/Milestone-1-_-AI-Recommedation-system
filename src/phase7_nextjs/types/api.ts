// Types aligned with Phase 6 API JSON contract

export interface RecommendationItem {
  id: string;
  rank: number;
  name: string;
  cuisine: string;
  rating: number;
  cost_for_two: number;
  explanation: string;
}

export interface Telemetry {
  latency_ms: number;
  provider: string;
  model: string;
  total_candidates: number;
  relaxed_filters: string[];
}

export interface RecommendationResponse {
  recommendations: RecommendationItem[];
  source: "llm" | "rule_based" | "no_candidates";
  counts: { returned: number; candidates: number };
  telemetry: Telemetry | null;
  messages: string[];
}

export interface Preferences {
  location: string;
  budget: string;
  cuisine: string;
  min_rating: number;
  additional_prefs: string;
}
