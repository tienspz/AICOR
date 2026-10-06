import { useEffect, useState } from 'react';
import Header from './components/Header';
import MetricCards from './components/MetricCards';
import EChartViewer from './components/EChartViewer';
import InOutBreakdownChart from './components/InOutBreakdownChart';
import RawMetricsChart from './components/RawMetricsChart';
import TimelineViewer from './components/TimelineViewer';
import PortfolioSimulator from './components/PortfolioSimulator';
import MethodologyModal from './components/MethodologyModal';
import Footer from './components/Footer';
import { fetchLiveStock, loadDashboardData } from './services/dataService';
import type { DashboardData } from './services/dataService';
import type { LiveStock } from './types/aicor';

type Tab = 'e' | 'inout' | 'raw';

const TABS: Array<{ key: Tab; label: string }> = [
  { key: 'e', label: 'Điểm hiệu suất E' },
  { key: 'inout', label: 'Phân rã In & Out' },
  { key: 'raw', label: 'Chỉ số thành phần thô' },
];

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [live, setLive] = useState<LiveStock | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('e');
  const [methodOpen, setMethodOpen] = useState(false);

  useEffect(() => {
    loadDashboardData()
      .then(setData)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Không tải được dữ liệu.'));
    fetchLiveStock().then(setLive);
  }, []);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
        <div className="max-w-md rounded-xl border border-rose-800 bg-rose-500/10 p-6 text-center">
          <p className="font-bold text-rose-300">Không tải được dữ liệu</p>
          <p className="mt-1 text-sm text-slate-300">{error}</p>
          <p className="mt-2 text-xs text-slate-400">
            Hãy chạy <code>npm run sync-data</code> trong thư mục frontend để sao chép 4 file JSON
            từ <code>data/processed/</code>.
          </p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="animate-pulse text-sm text-slate-400">Đang tải dữ liệu AICOR…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Header manifest={data.manifest} live={live} onOpenMethodology={() => setMethodOpen(true)} />
      <main className="mx-auto max-w-7xl space-y-8 px-4 py-6 sm:px-6">
        <MetricCards chart={data.chart} timeline={data.timeline} />

        <section aria-label="Biểu đồ đa chiều" className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Chế độ xem biểu đồ">
            {TABS.map((t) => (
              <button
                key={t.key}
                type="button"
                role="tab"
                aria-selected={tab === t.key}
                onClick={() => setTab(t.key)}
                className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition ${
                  tab === t.key
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          {tab === 'e' && <EChartViewer chart={data.chart} timeline={data.timeline} />}
          {tab === 'inout' && <InOutBreakdownChart chart={data.chart} />}
          {tab === 'raw' && <RawMetricsChart chart={data.chart} />}
        </section>

        <TimelineViewer timeline={data.timeline} />
        <PortfolioSimulator baseline={data.baseline} />
      </main>
      <Footer manifest={data.manifest} />
      {methodOpen && <MethodologyModal onClose={() => setMethodOpen(false)} />}
    </div>
  );
}
