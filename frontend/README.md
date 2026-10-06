# AICOR Frontend — Layer 3 Display (AICOR-020)

React + Vite + TypeScript + Tailwind CSS v4 + Recharts + lucide-react.
Dashboard tiêu thụ các JSON tiền tính toán của Layer 2, **không bao giờ tự tính lại E** (FR-14).

## Chạy nhanh

```powershell
cd frontend
npm install
npm run sync-data   # copy 4 JSON từ ../data/processed vào public/data
npm run dev         # http://localhost:5173
npm run build       # kiểm tra tsc + production build (tự sync-data trước)
```

## Nguồn dữ liệu

| File (`public/data/`) | Nội dung |
|---|---|
| `chart_series.json` | 18 quý × 3 công ty: `in_score`, `out_score`, `e_score`, spend, trends, product |
| `timeline_events.json` | 33 sự kiện `launch` / `funding` / `relationship` theo ngày tăng dần |
| `portfolio_baseline.json` | Trung vị E 4 quý gần nhất + disclaimer minh họa |
| `manifest.json` | `last_sync_utc`, trạng thái, phạm vi quý |

Chế độ dual-mode: mặc định đọc JSON tĩnh (deploy được GitHub Pages/Vercel, không cần
backend). Khi FastAPI chạy tại `http://localhost:8000`, badge giá MSFT tự lấy giá live
(kèm nhãn trễ 15 phút theo FR-12); offline thì hiển thị dấu `—` trung thực.

## Ghi chú tuân thủ SRS

- E/ In/ Out/ z-score/ MA4Q: hiển thị nguyên bản từ JSON (FR-14).
- Công cụ vốn: Score = Σ w × median(E 4Q) với median đọc từ JSON (FR-10), 3 slider luôn
  khóa tổng 100% (FR-09), disclaimer luôn hiển thị.
- Không dùng các diễn đạt ROI / “hiệu quả nhất” / nhân quả (Phụ lục C.9, D.1).
