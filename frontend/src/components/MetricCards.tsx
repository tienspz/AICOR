import { AlertTriangle } from 'lucide-react';
import type { ChartSeriesBundle, CompanyKey, TimelineBundle } from '../types/aicor';
import { COMPANY_KEYS, COMPANY_STYLE, formatMoney, formatScore } from '../services/dataService';

interface MetricCardsProps {
  chart: ChartSeriesBundle;
  timeline: TimelineBundle;
}

export default function MetricCards({ chart, timeline }: MetricCardsProps) {
  const latestQuarter = chart.quarters[chart.quarters.length - 1] ?? '—';
  return (
    <section aria-label="Thẻ tổng quan công ty">
      <div className="mb-3 flex items-baseline gap-2">
        <h2 className="text-base font-semibold text-white">Tổng quan quý gần nhất</h2>
        <span className="text-xs text-slate-400">Quý {latestQuarter} · giá trị đọc từ dữ liệu tiền tính toán</span>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {COMPANY_KEYS.map((key: CompanyKey) => {
          const entry = chart.companies[key];
          const latest = entry.series[entry.series.length - 1];
          const launches = timeline.events.filter(
            (e) => e.type === 'launch' && e.company_id === entry.company_id,
          ).length;
          const spend = key === 'MSFT' ? latest?.rnd_spend ?? null : latest?.ai_spend_est ?? null;
          const lowConfidence = (latest?.est_confidence ?? '').toLowerCase() === 'low';
          const e = latest?.e_score ?? null;
          const eTone = e === null ? 'text-slate-200' : e > 0 ? 'text-emerald-300' : e < 0 ? 'text-rose-300' : 'text-slate-200';
          return (
            <article
              key={key}
              className="rounded-xl border border-slate-800 bg-slate-900 p-4 shadow-sm"
            >
              <div className="mb-2 flex items-center justify-between">
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${COMPANY_STYLE[key].chip}`}
                >
                  {key === 'MSFT' ? 'Microsoft (MSFT)' : COMPANY_STYLE[key].name}
                </span>
                <span className="text-[11px] text-slate-500">{launches} sản phẩm đã ra mắt</span>
              </div>
              <div className={`text-3xl font-bold tabular-nums ${eTone}`}>
                {formatScore(e)}
                <span className="ml-2 align-middle text-xs font-medium text-slate-400">điểm E</span>
              </div>
              <dl className="mt-3 space-y-1 text-xs text-slate-300">
                <div className="flex justify-between">
                  <dt>In (đầu vào chuẩn hóa)</dt>
                  <dd className="font-semibold tabular-nums">{formatScore(latest?.in_score ?? null)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Out (đầu ra chuẩn hóa)</dt>
                  <dd className="font-semibold tabular-nums">{formatScore(latest?.out_score ?? null)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>{key === 'MSFT' ? 'Chi phí R&D quý' : 'Ước tính chi tiêu AI quý'}</dt>
                  <dd className="font-semibold tabular-nums">{formatMoney(spend)}</dd>
                </div>
                {key !== 'MSFT' && (
                  <div className="flex items-center justify-between">
                    <dt>Độ tin cậy ước tính</dt>
                    <dd className="inline-flex items-center gap-1 font-semibold">
                      {lowConfidence && <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />}
                      <span className={lowConfidence ? 'text-amber-300' : 'text-slate-200'}>
                        {latest?.est_confidence ?? '—'}
                        {lowConfidence ? ' (không dùng cho kết luận chính)' : ''}
                      </span>
                    </dd>
                  </div>
                )}
              </dl>
            </article>
          );
        })}
      </div>
    </section>
  );
}
