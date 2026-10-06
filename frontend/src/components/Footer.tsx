import type { Manifest } from '../types/aicor';

interface FooterProps {
  manifest: Manifest;
}

export default function Footer({ manifest }: FooterProps) {
  const utc = manifest.last_sync_utc;
  const local = (() => {
    const d = new Date(utc);
    return Number.isNaN(d.getTime()) ? utc : d.toLocaleString('vi-VN');
  })();
  return (
    <footer className="mt-8 border-t border-slate-800 bg-slate-950">
      <div className="mx-auto max-w-7xl space-y-1 px-4 py-5 text-xs text-slate-400 sm:px-6">
        <p className="font-semibold text-slate-300">
          AICOR — CMU Foundations of Software Engineering (v{manifest.version})
        </p>
        <p>
          Đồng bộ gần nhất (UTC): <span className="tabular-nums text-slate-200">{utc}</span> ·
          Giờ địa phương: <span className="tabular-nums text-slate-200">{local}</span> · Trạng thái:{' '}
          <span className="font-semibold text-emerald-300">{manifest.status}</span> ·{' '}
          {manifest.quarters_count} quý ({manifest.quarter_range.start} →{' '}
          {manifest.quarter_range.end})
        </p>
        <p>
          Web chỉ đọc dữ liệu đã tính từ JSON/manifest, không tự tính lại E (FR-14). Điểm E là chênh
          lệch tương đối so với lịch sử nội tại của từng công ty — không phải ROI, không chứng minh
          nhân quả.
        </p>
      </div>
    </footer>
  );
}
