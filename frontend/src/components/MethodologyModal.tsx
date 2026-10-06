import { useEffect } from 'react';
import { X } from 'lucide-react';

interface MethodologyModalProps {
  onClose: () => void;
}

export default function MethodologyModal({ onClose }: MethodologyModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Phương pháp luận AICOR"
    >
      <div
        className="aicor-scroll max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-slate-700 bg-slate-900 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <h2 className="text-lg font-bold text-white">Phương pháp luận AICOR (CMU SRS v5.1)</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng"
            className="rounded-lg bg-slate-800 p-1.5 text-slate-300 hover:bg-slate-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4 text-sm leading-relaxed text-slate-300">
          <div>
            <h3 className="mb-1 font-semibold text-white">1. Công thức điểm hiệu suất</h3>
            <p className="rounded-lg bg-slate-800 p-3 text-center font-mono text-[13px] text-indigo-200">
              z(x) = (x − mean) / std &nbsp;·&nbsp; Out = 0.6·z(Sản phẩm MA4Q) + 0.4·z(Trends MA4Q)
              <br />
              In = z(Chi tiêu) &nbsp;·&nbsp; E = Out − In
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Mọi chỉ số được chuẩn hóa z-score RIÊNG trong chuỗi thời gian của chính công ty đó
              (std = 0 → z = 0). Trọng số mặc định 0.6/0.4, kiểm tra độ nhạy với 0.5/0.5 và 0.7/0.3.
            </p>
          </div>
          <div>
            <h3 className="mb-1 font-semibold text-white">2. Diễn giải đúng điểm E</h3>
            <ul className="list-disc space-y-1 pl-5">
              <li>E &gt; 0: đầu ra tăng tương đối nhanh hơn đầu vào so với mức lịch sử của công ty.</li>
              <li>E &lt; 0: đầu vào tăng tương đối nhanh hơn đầu ra so với mức lịch sử của công ty.</li>
              <li>E ≈ 0: mức thay đổi tương đối của hai phía gần nhau.</li>
            </ul>
          </div>
          <div>
            <h3 className="mb-1 font-semibold text-white">3. E không phải là gì</h3>
            <p>
              E <strong>không phải</strong> ROI, lợi nhuận, tỷ lệ hoàn vốn hay bằng chứng nhân quả.
              Không dùng E để khẳng định công ty nào “hiệu quả nhất”, “sinh lời cao nhất”, hay khái
              quát cho toàn ngành AI.
            </p>
          </div>
          <div>
            <h3 className="mb-1 font-semibold text-white">4. Giới hạn dữ liệu cần biết</h3>
            <ul className="list-disc space-y-1 pl-5 text-[13px]">
              <li>R&amp;D của Microsoft bao gồm nhiều mảng, không chỉ AI.</li>
              <li>Chi tiêu AI của OpenAI/Anthropic là ước tính từ nguồn công khai, kèm mức độ tin cậy.</li>
              <li>Điểm sản phẩm dựa trên blog/changelog chính thức (rubric A/B/C), có thể phản ánh cách công bố.</li>
              <li>Google Trends là chỉ số tương đối, chịu nhiễu truyền thông và cách chọn từ khóa.</li>
              <li>Số quý quan sát còn nhỏ; ba công ty không đại diện toàn ngành.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
