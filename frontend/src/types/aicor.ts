/**
 * TypeScript contracts for the Layer-2 precomputed JSON bundles.
 * Field-for-field compatible with src/computation/exporter.py output.
 * FR-14: the frontend only READS these values — it never recomputes E.
 */

export type CompanyKey = 'MSFT' | 'OpenAI' | 'Anthropic';

export interface QuarterPoint {
  quarter: string;
  in_score: number | null;
  out_score: number | null;
  e_score: number | null;
  rnd_spend: number | null;
  ai_spend_est: number | null;
  est_confidence: string | null;
  trends_qavg: number | null;
  product_score: number | null;
  product_ma4q: number | null;
  trends_ma4q: number | null;
  valid_from: string | null;
}

export interface CompanySeries {
  company_id: number;
  name: string;
  series: QuarterPoint[];
}

export interface ChartSeriesBundle {
  generated_at: string;
  quarters: string[];
  companies: Record<CompanyKey, CompanySeries>;
  note: string;
}

export type TimelineEventType = 'launch' | 'funding' | 'relationship';

export interface TimelineEvent {
  date: string;
  quarter: string;
  type: TimelineEventType;
  company_id: number | null;
  company_name: string | null;
  title: string;
  category?: string | null;
  points?: number | null;
  amount?: number | null;
  valuation?: number | null;
  parties?: string;
  rel_type?: string | null;
  quote?: string | null;
  source_url: string;
}

export interface TimelineBundle {
  generated_at: string;
  count: number;
  events: TimelineEvent[];
}

export interface PortfolioBaseline {
  generated_at: string;
  reference_window: string[];
  method: string;
  medians: Record<CompanyKey, number | null>;
  disclaimer: string;
}

export interface ManifestCompany {
  id: number;
  name: string;
  ticker: string;
}

export interface Manifest {
  system: string;
  version: string;
  last_sync_utc: string;
  status: string;
  quarters_count: number;
  quarter_range: { start: string; end: string };
  companies: ManifestCompany[];
  default_weights: { product: number; trends: number };
  artifacts: Record<string, string>;
}

/** FR-12 live quote payload (FastAPI GET /api/stock/msft/live). */
export interface LiveStock {
  symbol: string;
  price: number | null;
  currency: string;
  latency_minutes: number;
  source: string;
  stale_fallback?: boolean;
}
