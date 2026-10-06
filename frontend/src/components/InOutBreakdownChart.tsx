import { useMemo, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ChartSeriesBundle, CompanyKey } from '../types/aicor';
import { COMPANY_KEYS, COMPANY_STYLE } from '../services/dataService';

interface InOutBreakdownChartProps {
  chart: ChartSeriesBundle;
}

function InOutTooltip(props: any) {
  const { active, payload, label, companyName } = props as {
    active?: boolean;
    payload?: Array<{ dataKey: string | number; value: number | null }>;
    label?: string;
    companyName: string;
  };
  if (!active || !payload || payload.length === 0 || !label) return null;
  const get = (k: string) => payload.find((p) => String(p.dataKey) === k)?.value ?? '—';
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/95 p-3 text-xs shadow-xl">
      <p className="mb-1 font-bold text-white">
        {companyName} · {label}
      </p>
      <p className="tabular-nums text-amber-300">In: {String(get('In'))}</p>
      <p className="tabular-nums text-sky-300">Out: {String(get('Out'))}</p>
      <p className="mt-1 text-slate-400">Khoảng cách đứng giữa hai đường chính là E (Out − In).</p>
    </div>
  );
}

export default function InOutBreakdownChart({ chart }: InOutBreakdownChartProps) {
  const [company, setCompany] = useState<CompanyKey>('MSFT');

  const rows = useMemo(
    () =>
      chart.quarters.map((q) => {
        const p = chart.companies[company].series.find((s) => s.quarter === q);
        return { quarter: q, In: p?.in_score ?? null, Out: p?.out_score ?? null };
      }),
    [chart, company],
  );

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        {COMPANY_KEYS.map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setCompany(k)}
            className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 transition ${
              company === k ? COMPANY_STYLE[k].chip : 'bg-slate-800 text-slate-400 ring-slate-700'
            }`}
          >
            {COMPANY_STYLE[k].name}
          </button>
        ))}
      </div>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="quarter" tick={{ fontSize: 11, fill: '#94a3b8' }} interval={1} />
            <YAxis
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              domain={['auto', 'auto']}
              tickFormatter={(v: number) => v.toFixed(1)}
            />
            <Tooltip content={<InOutTooltip companyName={COMPANY_STYLE[company].name} />} />
            <ReferenceLine y={0} stroke="#64748b" strokeDasharray="4 4" />
            <Line type="monotone" dataKey="In" stroke="#fbbf24" strokeWidth={2} dot={false} connectNulls />
            <Line type="monotone" dataKey="Out" stroke="#38bdf8" strokeWidth={2} dot={false} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex gap-4 text-xs text-slate-400">
        <span>
          <span className="mr-1 inline-block h-2 w-4 rounded bg-amber-400" /> In — đầu vào chuẩn hóa
          (z-score chi tiêu)
        </span>
        <span>
          <span className="mr-1 inline-block h-2 w-4 rounded bg-sky-400" /> Out — đầu ra chuẩn hóa
          (0.6 sản phẩm + 0.4 trends)
        </span>
      </div>
    </div>
  );
}
