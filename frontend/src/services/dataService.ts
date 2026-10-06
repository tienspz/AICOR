/**
 * Dual-mode data access (FR-14, NFR-01, IF-6/IF-7):
 * - Default: static precomputed JSON bundles in public/data (standalone,
 *   deployable to GitHub Pages / Vercel with no backend).
 * - Live enhancement: FastAPI GET /api/stock/msft/live when a backend is
 *   reachable on localhost:8000; silent fallback otherwise.
 */
import type {
  ChartSeriesBundle,
  CompanyKey,
  LiveStock,
  Manifest,
  PortfolioBaseline,
  TimelineBundle,
} from '../types/aicor';

export interface DashboardData {
  chart: ChartSeriesBundle;
  timeline: TimelineBundle;
  baseline: PortfolioBaseline;
  manifest: Manifest;
}

export const COMPANY_KEYS: CompanyKey[] = ['MSFT', 'OpenAI', 'Anthropic'];

export const COMPANY_STYLE: Record<CompanyKey, { name: string; color: string; chip: string }> = {
  MSFT: { name: 'Microsoft', color: '#38bdf8', chip: 'bg-sky-500/15 text-sky-300 ring-sky-500/30' },
  OpenAI: { name: 'OpenAI', color: '#34d399', chip: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30' },
  Anthropic: { name: 'Anthropic', color: '#c084fc', chip: 'bg-purple-500/15 text-purple-300 ring-purple-500/30' },
};

const API_BASE = 'http://localhost:8000/api';

async function fetchStatic<T>(file: string): Promise<T> {
  const url = `${import.meta.env.BASE_URL}data/${file}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Không tải được dữ liệu tĩnh ${file} (HTTP ${res.status}).`);
  }
  return (await res.json()) as T;
}

export async function loadDashboardData(): Promise<DashboardData> {
  const [chart, timeline, baseline, manifest] = await Promise.all([
    fetchStatic<ChartSeriesBundle>('chart_series.json'),
    fetchStatic<TimelineBundle>('timeline_events.json'),
    fetchStatic<PortfolioBaseline>('portfolio_baseline.json'),
    fetchStatic<Manifest>('manifest.json'),
  ]);
  return { chart, timeline, baseline, manifest };
}

/** Returns live MSFT quote, or null when no backend is reachable (offline-safe). */
export async function fetchLiveStock(timeoutMs = 4000): Promise<LiveStock | null> {
  try {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    const res = await fetch(`${API_BASE}/stock/msft/live`, { signal: ctrl.signal });
    clearTimeout(timer);
    if (!res.ok) return null;
    return (await res.json()) as LiveStock;
  } catch {
    return null;
  }
}

/** Spend actually recorded for a quarter: MSFT R&D, others AI-spend estimate. */
export function spendOf(point: {
  rnd_spend: number | null;
  ai_spend_est: number | null;
}): number | null {
  return point.rnd_spend ?? point.ai_spend_est;
}

export function formatMoney(v: number | null): string {
  if (v === null || Number.isNaN(v)) return '—';
  if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${v.toFixed(0)}`;
}

export function formatScore(v: number | null, digits = 3): string {
  if (v === null || Number.isNaN(v)) return '—';
  const sign = v > 0 ? '+' : '';
  return `${sign}${v.toFixed(digits)}`;
}
