import { useMemo, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ChartSeriesBundle } from '../types/aicor';
import { COMPANY_KEYS, COMPANY_STYLE, formatMoney, spendOf } from '../services/dataService';

interface RawMetricsChartProps {
  chart: ChartSeriesBundle;
}

type Metric = 'product_score' | 'trends_qavg' | 'spend';

const METRIC_LABEL: Record<Metric, string> = {
  product_score: 'Điểm sản phẩm quý (3A + 2B + 1C)',
  trends_qavg: 'Google Trends trung bình quý (0–100)',
  spend: 'Chi tiêu quý (R&D / ước tính AI)',
};

function valueOf(metric: Metric, point: { product_score: number | null; trends_qavg: number | null; rnd_spend: number | null; ai_spend_est: number | null }): number | null {
  if (metric === 'spend') return spendOf(point);
  return point[metric];
}

export default function RawMetricsChart({ chart }: RawMetricsChartProps) {
  const [metric, setMetric] = useState<Metric>('product_score');

  const rows = useMemo(
    () =>
      chart.quarters.map((q) => {
        const row: Record<string, string | number | null> = { quarter: q };
        for (const k of COMPANY_KEYS) {
          const p = chart.companies[k].series.find((s) => s.quarter === q);
          row[k] = p ? valueOf(metric, p) : null;
        }
        return row;
      }),
    [chart, metric],
  );

  const isMoney = metric === 'spend';

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        {(Object.keys(METRIC_LABEL) as Metric[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMetric(m)}
            className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 transition ${
              metric === m
                ? 'bg-indigo-500/15 text-indigo-300 ring-indigo-500/30'
                : 'bg-slate-800 text-slate-400 ring-slate-700'
            }`}
          >
            {METRIC_LABEL[m]}
          </button>
        ))}
      </div>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="quarter" tick={{ fontSize: 11, fill: '#94a3b8' }} interval={1} />
            <YAxis
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              width={isMoney ? 64 : 40}
              tickFormatter={(v: number) => (isMoney ? `$${(v / 1e9).toFixed(1)}B` : `${v}`)}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', fontSize: 12 }}
              formatter={(value: any, name: any) => [
                isMoney ? formatMoney(Number(value)) : String(value),
                COMPANY_STYLE[name as keyof typeof COMPANY_STYLE]?.name ?? String(name),
              ]}
              labelStyle={{ color: '#e2e8f0', fontWeight: 'bold' }}
            />
            {COMPANY_KEYS.map((k) => (
              <Line
                key={k}
                type="monotone"
                dataKey={k}
                name={COMPANY_STYLE[k].name}
                stroke={COMPANY_STYLE[k].color}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-slate-400">
        Chỉ số thô trước chuẩn hóa, đọc trực tiếp từ dữ liệu tiền tính toán: điểm sản phẩm theo
        rubric A/B/C, Trends trung bình quý, và chi tiêu (Microsoft: R&amp;D — OpenAI/Anthropic:
        ước tính AI).
      </p>
    </div>
  );
}
