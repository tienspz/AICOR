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
import type { ChartSeriesBundle, CompanyKey, TimelineBundle } from '../types/aicor';
import { COMPANY_KEYS, COMPANY_STYLE } from '../services/dataService';

interface EChartViewerProps {
  chart: ChartSeriesBundle;
  timeline: TimelineBundle;
}

interface Row {
  quarter: string;
  [k: string]: string | number | null;
}

/** Tooltip hiển thị E / In / Out đọc trực tiếp từ JSON + sự kiện cùng quý. */
function ETooltip(props: any) {
  const { active, payload, label, pointsByQuarter, eventsByQuarter } = props as {
    active?: boolean;
    payload?: Array<{ dataKey: string | number }>;
    label?: string;
    pointsByQuarter: Map<string, Map<CompanyKey, { e: number | null; i: number | null; o: number | null }>>;
    eventsByQuarter: Map<string, string[]>;
  };
  if (!active || !payload || payload.length === 0 || !label) return null;
  const pts = pointsByQuarter.get(label);
  const evts = eventsByQuarter.get(label) ?? [];
  const shown = payload
    .map((p) => String(p.dataKey) as CompanyKey)
    .filter((k) => pts?.has(k));
  return (
    <div className="max-w-xs rounded-lg border border-slate-700 bg-slate-900/95 p-3 text-xs shadow-xl">
      <p className="mb-1 font-bold text-white">Quý {label}</p>
      {shown.map((k) => {
        const v = pts?.get(k);
        return (
          <p key={k} className="tabular-nums text-slate-200">
            <span style={{ color: COMPANY_STYLE[k].color }}>●</span> {COMPANY_STYLE[k].name}: E{' '}
            {v?.e ?? '—'} · In {v?.i ?? '—'} · Out {v?.o ?? '—'}
          </p>
        );
      })}
      {evts.length > 0 && (
        <div className="mt-1 border-t border-slate-700 pt-1 text-slate-400">
          <p className="font-semibold text-slate-300">Sự kiện nổi bật:</p>
          {evts.slice(0, 3).map((t) => (
            <p key={t} className="truncate">
              • {t}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

export default function EChartViewer({ chart, timeline }: EChartViewerProps) {
  const [visible, setVisible] = useState<Record<CompanyKey, boolean>>({
    MSFT: true,
    OpenAI: true,
    Anthropic: true,
  });

  const toggle = (k: CompanyKey) => setVisible((v) => ({ ...v, [k]: !v[k] }));

  const rows: Row[] = useMemo(
    () =>
      chart.quarters.map((q) => {
        const row: Row = { quarter: q };
        for (const k of COMPANY_KEYS) {
          const p = chart.companies[k].series.find((s) => s.quarter === q);
          row[k] = p?.e_score ?? null;
        }
        return row;
      }),
    [chart],
  );

  const pointsByQuarter = useMemo(() => {
    const m = new Map<string, Map<CompanyKey, { e: number | null; i: number | null; o: number | null }>>();
    for (const q of chart.quarters) {
      const inner = new Map<CompanyKey, { e: number | null; i: number | null; o: number | null }>();
      for (const k of COMPANY_KEYS) {
        const p = chart.companies[k].series.find((s) => s.quarter === q);
        inner.set(k, { e: p?.e_score ?? null, i: p?.in_score ?? null, o: p?.out_score ?? null });
      }
      m.set(q, inner);
    }
    return m;
  }, [chart]);

  const eventsByQuarter = useMemo(() => {
    const m = new Map<string, string[]>();
    for (const e of timeline.events) {
      const list = m.get(e.quarter) ?? [];
      list.push(e.title);
      m.set(e.quarter, list);
    }
    return m;
  }, [timeline]);

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        {COMPANY_KEYS.map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => toggle(k)}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 transition ${
              visible[k] ? COMPANY_STYLE[k].chip : 'bg-slate-800 text-slate-500 ring-slate-700'
            }`}
          >
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: visible[k] ? COMPANY_STYLE[k].color : '#475569' }}
            />
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
            <Tooltip
              content={
                <ETooltip pointsByQuarter={pointsByQuarter} eventsByQuarter={eventsByQuarter} />
              }
            />
            <ReferenceLine y={0} stroke="#64748b" strokeDasharray="4 4" label={{ value: 'E = 0', fill: '#64748b', fontSize: 11 }} />
            {COMPANY_KEYS.filter((k) => visible[k]).map((k) => (
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
        Đường E = 0 là ngưỡng cân bằng tương đối: E &gt; 0 nghĩa là trong quý đó đầu ra tăng
        tương đối nhanh hơn đầu vào so với mức lịch sử của chính công ty (và ngược lại).
      </p>
    </div>
  );
}
