import { useMemo, useState } from 'react';
import { RotateCcw, Wallet } from 'lucide-react';
import type { CompanyKey, PortfolioBaseline } from '../types/aicor';
import { COMPANY_KEYS, COMPANY_STYLE } from '../services/dataService';

interface PortfolioSimulatorProps {
  baseline: PortfolioBaseline;
}

type Weights = Record<CompanyKey, number>;

const DEFAULT_WEIGHTS: Weights = { MSFT: 34, OpenAI: 33, Anthropic: 33 };

/**
 * FR-09/FR-10: 3 sliders whose sum is always locked at 100%.
 * Score = Σ w_c × median(E_c, 4Q) using PRECOMPUTED medians from JSON —
 * no E/z-score math is performed here (FR-14).
 */
export default function PortfolioSimulator({ baseline }: PortfolioSimulatorProps) {
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS);
  const medians = baseline.medians;
  const missing = COMPANY_KEYS.filter((k) => medians[k] === null);

  const adjust = (key: CompanyKey, pct: number) => {
    const value = Math.min(100, Math.max(0, Math.round(pct)));
    const others = COMPANY_KEYS.filter((k) => k !== key);
    const otherSum = others.reduce((s, k) => s + weights[k], 0);
    const rest = 100 - value;
    const next = { ...weights, [key]: value };
    if (otherSum > 0) {
      let acc = 0;
      others.forEach((k, i) => {
        if (i === others.length - 1) {
          next[k] = Math.round((rest - acc) * 10) / 10;
        } else {
          next[k] = Math.round(((weights[k] / otherSum) * rest) * 10) / 10;
          acc += next[k];
        }
      });
    } else {
      const share = Math.round((rest / others.length) * 10) / 10;
      others.forEach((k, i) => {
        next[k] = i === others.length - 1 ? Math.round((rest - share * i) * 10) / 10 : share;
      });
    }
    setWeights(next);
  };

  const score = useMemo(() => {
    if (missing.length > 0) return null;
    return COMPANY_KEYS.reduce((s, k) => s + (weights[k] / 100) * (medians[k] ?? 0), 0);
  }, [weights, medians, missing.length]);

  const total = COMPANY_KEYS.reduce((s, k) => s + weights[k], 0);

  return (
    <section aria-label="Công cụ phân bổ vốn minh họa">
      <div className="mb-3 flex items-center gap-2">
        <Wallet className="h-4 w-4 text-indigo-300" />
        <h2 className="text-base font-semibold text-white">Công cụ phân bổ vốn (minh họa)</h2>
      </div>
      <div className="grid gap-4 lg:grid-cols-5">
        <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-4 lg:col-span-3">
          {COMPANY_KEYS.map((k) => (
            <div key={k}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200">{COMPANY_STYLE[k].name}</span>
                <span className="font-bold tabular-nums text-white">{weights[k].toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                step={1}
                value={Math.round(weights[k])}
                onChange={(e) => adjust(k, Number(e.target.value))}
                aria-label={`Tỷ trọng ${COMPANY_STYLE[k].name}`}
                className="aicor-slider"
              />
            </div>
          ))}
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>
              Tổng tỷ trọng: <strong className="tabular-nums text-white">{total.toFixed(1)}%</strong>{' '}
              (luôn khóa ở 100%)
            </span>
            <button
              type="button"
              onClick={() => setWeights(DEFAULT_WEIGHTS)}
              className="inline-flex items-center gap-1 rounded-lg bg-slate-800 px-2.5 py-1 font-semibold text-slate-300 ring-1 ring-slate-700 hover:bg-slate-700"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Đặt lại
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 lg:col-span-2">
          <p className="text-xs text-slate-400">
            Cửa sổ tham chiếu: {baseline.reference_window.join(' → ')}
          </p>
          <ul className="mt-2 space-y-1 text-xs text-slate-300">
            {COMPANY_KEYS.map((k) => (
              <li key={k} className="flex justify-between tabular-nums">
                <span>
                  median(E) {COMPANY_STYLE[k].name} × {(weights[k] / 100).toFixed(3)}
                </span>
                <strong>{medians[k] === null ? 'thiếu dữ liệu' : medians[k]?.toFixed(3)}</strong>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm text-slate-400">Điểm danh mục minh họa:</p>
          <p className="text-3xl font-bold tabular-nums text-indigo-300">
            {score === null ? '—' : `${score >= 0 ? '+' : ''}${score.toFixed(4)}`}
          </p>
          {missing.length > 0 && (
            <p className="mt-1 text-xs text-amber-300">
              Thiếu dữ liệu E của {missing.join(', ')} trong cửa sổ tham chiếu — không tạo kết quả
              giả.
            </p>
          )}
          <div className="mt-3 rounded-lg border border-amber-600/50 bg-amber-500/10 p-3 text-xs leading-relaxed text-amber-200">
            <p className="font-bold">⚠️ Công cụ minh họa, không phải khuyến nghị đầu tư.</p>
            <p className="mt-1">
              Điểm danh mục dựa trên trung vị E của 4 quý gần nhất. Điểm E là chỉ số hiệu suất
              tương đối so với lịch sử nội tại của từng công ty, không phản ánh tỷ suất sinh lời
              tài chính (ROI) thực tế.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
