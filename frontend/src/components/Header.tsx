import { Activity, FlaskConical } from 'lucide-react';
import type { LiveStock, Manifest } from '../types/aicor';

interface HeaderProps {
  manifest: Manifest;
  live: LiveStock | null;
  onOpenMethodology: () => void;
}

export default function Header({ manifest, live, onOpenMethodology }: HeaderProps) {
  const synced = manifest.status === 'success';
  return (
    <header className="border-b border-slate-800 bg-slate-950/90">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white">AICOR</h1>
            <p className="text-xs text-slate-400">
              AI Investment &amp; Outcomes Comparative Analytics · CMU SRS v{manifest.version}
            </p>
          </div>
        </div>

        <div className="ml-auto flex flex-wrap items-center gap-2">
          <div
            className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5"
            title={live?.source ?? 'Mở backend FastAPI (localhost:8000) để xem giá trực tiếp'}
          >
            <span className="text-xs font-semibold text-slate-300">MSFT</span>
            <span className="text-sm font-bold text-white">
              {live?.price != null ? `$${live.price.toFixed(2)}` : '—'}
            </span>
            <span className="text-[11px] text-slate-400">⏱️ Yahoo Finance (trễ 15 phút)</span>
          </div>

          <span
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium ${
              synced
                ? 'border-emerald-700 bg-emerald-500/10 text-emerald-300'
                : 'border-amber-700 bg-amber-500/10 text-amber-300'
            }`}
          >
            <span className={`h-2 w-2 rounded-full ${synced ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            {synced ? 'Đồng bộ: Thành công' : `Trạng thái: ${manifest.status}`}
          </span>

          <button
            type="button"
            onClick={onOpenMethodology}
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
          >
            <FlaskConical className="h-4 w-4" />
            Phương pháp luận
          </button>
        </div>
      </div>
    </header>
  );
}
