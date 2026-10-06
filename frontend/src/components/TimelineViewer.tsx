import { useState } from 'react';
import { DollarSign, ExternalLink, Rocket, Users } from 'lucide-react';
import type { TimelineBundle, TimelineEventType } from '../types/aicor';
import { formatMoney } from '../services/dataService';

interface TimelineViewerProps {
  timeline: TimelineBundle;
}

type Filter = 'all' | TimelineEventType;

const FILTERS: Array<{ key: Filter; label: string }> = [
  { key: 'all', label: 'Tất cả' },
  { key: 'launch', label: 'Ra mắt sản phẩm' },
  { key: 'funding', label: 'Vòng gọi vốn' },
  { key: 'relationship', label: 'Quan hệ' },
];

function EventIcon({ type }: { type: TimelineEventType }) {
  if (type === 'launch') return <Rocket className="h-4 w-4 text-sky-300" />;
  if (type === 'funding') return <DollarSign className="h-4 w-4 text-emerald-300" />;
  return <Users className="h-4 w-4 text-purple-300" />;
}

export default function TimelineViewer({ timeline }: TimelineViewerProps) {
  const [filter, setFilter] = useState<Filter>('all');
  const counts = (t: TimelineEventType) => timeline.events.filter((e) => e.type === t).length;
  const shown = timeline.events.filter((e) => filter === 'all' || e.type === filter);

  return (
    <section aria-label="Dòng thời gian sự kiện">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h2 className="text-base font-semibold text-white">Dòng thời gian sự kiện</h2>
        <span className="text-xs text-slate-400">{timeline.count} sự kiện · sắp xếp theo ngày</span>
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        {FILTERS.map((f) => {
          const n = f.key === 'all' ? timeline.count : counts(f.key);
          return (
            <button
              key={f.key}
              type="button"
              onClick={() => setFilter(f.key)}
              className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 transition ${
                filter === f.key
                  ? 'bg-indigo-500/15 text-indigo-300 ring-indigo-500/30'
                  : 'bg-slate-800 text-slate-400 ring-slate-700'
              }`}
            >
              {f.label} ({n})
            </button>
          );
        })}
      </div>
      <ol className="aicor-scroll max-h-96 space-y-2 overflow-y-auto pr-1">
        {shown.map((e) => (
          <li
            key={`${e.type}-${e.date}-${e.title}`}
            className="flex gap-3 rounded-xl border border-slate-800 bg-slate-900 p-3"
          >
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800">
              <EventIcon type={e.type} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs tabular-nums text-slate-400">{e.date}</span>
                <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[11px] font-semibold text-slate-300">
                  {e.quarter}
                </span>
                {e.company_name && (
                  <span className="text-[11px] font-medium text-slate-400">{e.company_name}</span>
                )}
                {e.type === 'launch' && e.category && (
                  <span className="rounded bg-sky-500/15 px-1.5 py-0.5 text-[11px] font-bold text-sky-300 ring-1 ring-sky-500/30">
                    Nhóm {e.category} · {e.points}đ
                  </span>
                )}
                {e.type === 'relationship' && e.rel_type && (
                  <span className="rounded bg-purple-500/15 px-1.5 py-0.5 text-[11px] font-semibold text-purple-300 ring-1 ring-purple-500/30">
                    {e.rel_type}
                  </span>
                )}
              </div>
              <p className="mt-1 truncate text-sm font-semibold text-white" title={e.title}>
                {e.title}
              </p>
              {e.type === 'funding' && (
                <p className="text-xs tabular-nums text-slate-300">
                  Gọi vốn {formatMoney(e.amount ?? null)}
                  {e.valuation != null ? ` · Định giá ${formatMoney(e.valuation)}` : ''}
                </p>
              )}
              {e.type === 'relationship' && e.quote && (
                <p className="mt-0.5 line-clamp-2 text-xs italic text-slate-400">“{e.quote}”</p>
              )}
              {e.source_url && (
                <a
                  href={e.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex items-center gap-1 text-[11px] text-indigo-400 hover:text-indigo-300"
                >
                  <ExternalLink className="h-3 w-3" /> Nguồn kiểm chứng
                </a>
              )}
            </div>
          </li>
        ))}
      </ol>
      <p className="mt-2 text-xs text-slate-500">
        Hệ thống không tự kết luận sự kiện nào gây ra thay đổi nào — người xem tự đối chiếu
        timeline với đồ thị E (FR-08).
      </p>
    </section>
  );
}
