# Kế hoạch & Đặc tả Kỹ thuật Triển khai Layer 3: React Web Application (AICOR-020)
*(Tài liệu tham chiếu chuẩn CMU SRS v5.1 & Hướng dẫn Triển khai cho Muse Spark 1.3 / OpenCode)*

**Mã dự án:** AICOR  
**Mã task:** AICOR-020 (P1)  
**Tài liệu gốc tối thượng:** [PROJECT_SPEC_CMU.md](PROJECT_SPEC_CMU.md)  
**Mục tiêu:** Xây dựng ứng dụng web React (Layer 3 — Display) tiêu thụ dữ liệu tiền tính toán từ Layer 2, trực quan hóa điểm hiệu suất đầu tư AI ($E$), phân rã $In$/$Out$, dòng thời gian 33 sự kiện, và công cụ mô phỏng phân bổ danh mục đầu tư minh họa.

---

## 🎯 1. Bối cảnh & Nguyên tắc Cốt lõi (Invariants)

### 1.1 Trạng thái Dữ liệu Hiện tại (Đã sẵn sàng 100%)
Toàn bộ backend Layer 1 (Crawl) và Layer 2 (Clean, Compute, SQLite, Exporter, API) đã hoàn tất (35/35 pytest pass). Dữ liệu tính toán đã được kết xuất sẵn sàng tại thư mục `data/processed/`:

1. **`data/processed/chart_series.json`**:
   - `quarters`: Mảng 18 quý (`["2022-Q1", ..., "2026-Q2"]`).
   - `companies`: Dữ liệu 3 công ty (`MSFT`, `OpenAI`, `Anthropic`). Mỗi công ty có mảng 18 bản ghi quý gồm: `quarter`, `in_score`, `out_score`, `e_score`, `rnd_spend`, `ai_spend_est`, `est_confidence`, `trends_qavg`, `product_score`, `product_ma4q`, `trends_ma4q`, `valid_from`.
   - Tất cả giá trị số đã được xử lý an toàn (không có `NaN`/`Infinity`, giá trị trống là `null`).
2. **`data/processed/timeline_events.json`**:
   - 33 sự kiện sắp xếp theo thứ tự thời gian (`date` tăng dần).
   - Phân loại: `launch` (sản phẩm A/B/C kèm điểm), `funding` (vòng gọi vốn kèm số tiền/định giá), `relationship` (quan hệ hợp tác/đầu tư/cạnh tranh kèm trích dẫn).
3. **`data/processed/portfolio_baseline.json`**:
   - `reference_window`: 4 quý gần nhất (`["2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]`).
   - `medians`: Trung vị điểm $E$ trong 4 quý gần nhất của từng công ty (`MSFT: -1.304`, `OpenAI: -1.661`, `Anthropic: -1.296`).
   - `disclaimer`: *"Công cụ minh họa, không phải khuyến nghị đầu tư."*
4. **`data/processed/manifest.json`**:
   - Metadata đồng bộ hệ thống: `system: "AICOR"`, `version: "5.1"`, `last_sync_utc`, `quarters_count: 18`, `quarter_range`.
5. **FastAPI Backend (Tùy chọn)**:
   - Chạy tại `http://localhost:8000/api` với các endpoint: `/health`, `/facts`, `/events`, `/sensitivity`, `/stock/msft/live`, `/simulate-portfolio`.
   - **Frontend phải hỗ trợ Dual-Mode:** Mặc định đọc trực tiếp các tệp JSON tĩnh (đảm bảo chạy standalone không cần backend, deploy được lên GitHub Pages/Vercel theo IF-6 và NFR-02); tự động kết nối API FastAPI khi có backend online.

---

### 1.2 Bốn Điều Răn Bắt Buộc (Strict Invariants)

1. **FR-14 — TUYỆT ĐỐI KHÔNG TÍNH LẠI ĐIỂM $E$ TRÊN REACT**:
   - Mọi giá trị $E$, $In$, $Out$, z-score, trung bình động 4Q đều **phải lấy nguyên bản từ JSON**.
   - React chỉ đóng vai trò tiêu thụ và hiển thị (Layer 3 — Display). Không được lập trình lại công thức z-score hay tính toán lại $E$ trong JavaScript/TypeScript.
2. **Ý NGHĨA KHOA HỌC CỦA ĐIỂM $E$ (Phụ lục C & D)**:
   - $E = Out - In$ là **chênh lệch tương đối theo chuỗi thời gian của chính công ty đó**, KHÔNG PHẢI ROI, không phải lợi nhuận tài chính, và KHÔNG CHỨNG MINH QUAN HỆ NHÂN QUẢ.
   - $E > 0$: Trong quý đó, đầu ra tăng tương đối nhanh hơn đầu vào so với mức lịch sử của chính công ty.
   - $E < 0$: Trong quý đó, đầu vào tăng tương đối nhanh hơn đầu ra so với mức lịch sử của chính công ty.
   - Trên UI không dùng các từ: *"công ty đầu tư hiệu quả nhất"*, *"ROI"*, *"sinh lời cao nhất"*.
3. **FR-09 & FR-10 — DISCLAIMER BẮT BUỘC TRÊN CÔNG CỤ PHÂN BỔ VỐN**:
   - Công cụ phân bổ danh mục phải có 3 thanh trượt cho Microsoft, OpenAI, Anthropic với tổng trọng số luôn bằng $100\%$ ($w_1 + w_2 + w_3 = 1.0$).
   - Công thức tính điểm danh mục: $\text{Portfolio Score} = \sum w_c \times \text{median}(E_{c, 4Q})$.
   - Nhãn bắt buộc phải luôn hiển thị nổi bật bên cạnh kết quả:
     > **"Công cụ minh họa, không phải khuyến nghị đầu tư."**
4. **FR-12 — NHÃN ĐỘ TRỄ GIÁ CỔ PHIẾU**:
   - Badge giá cổ phiếu MSFT phải hiển thị rõ thông tin độ trễ: **"Yahoo Finance (trễ 15 phút)"**.

---

## 🏗️ 2. Kiến trúc & Công nghệ Đề xuất cho Frontend

- **Vị trí thư mục:** `frontend/` (nằm ở thư mục gốc của repository).
- **Tech Stack:**
  - **Framework:** Vite + React (TypeScript hoặc JavaScript ES6+).
  - **Styling:** Tailwind CSS (hoặc Vanilla CSS Modules cao cấp), hỗ trợ Dark Mode / Financial High-Contrast Palette.
  - **Iconography:** `lucide-react`.
  - **Biểu đồ (Charts):** `recharts` (mượt mà, tương thích React hoàn hảo, hỗ trợ tooltip, dual-axis, responsive).
- **Cấu trúc Thư mục Chi tiết:**
  ```text
  frontend/
  ├── package.json
  ├── vite.config.ts
  ├── index.html
  ├── public/
  │   └── data/                       # Chứa 4 file JSON precomputed
  │       ├── chart_series.json
  │       ├── timeline_events.json
  │       ├── portfolio_baseline.json
  │       └── manifest.json
  └── src/
      ├── main.tsx
      ├── App.tsx
      ├── index.css
      ├── types/
      │   └── aicor.ts                # TypeScript interfaces cho các JSON bundles
      ├── services/
      │   └── dataService.ts          # Tải dữ liệu từ public/data/*.json, fallback API
      └── components/
          ├── Header.tsx              # Tên dự án, version 5.1, Live stock MSFT badge (15m latency)
          ├── MetricCards.tsx         # Cards tóm tắt 3 công ty: Latest E, In, Out, Product score
          ├── EChartViewer.tsx        # Biểu đồ E-score theo thời gian (2022-Q1 đến 2026-Q2)
          ├── InOutBreakdownChart.tsx # Biểu đồ phân rã In (R&D/Spend) vs Out (Product + Trends)
          ├── TimelineViewer.tsx      # Danh sách 33 sự kiện (filter: Launch, Funding, Relationship)
          ├── PortfolioSimulator.tsx  # 3 thanh trượt (tổng 100%), tính điểm, Disclaimer nổi bật
          ├── MethodologyModal.tsx    # Modal giải thích phương pháp luận, ý nghĩa E, các giới hạn D.1-D.8
          └── Footer.tsx              # Manifest sync time (UTC & Local), trạng thái hệ thống
  ```

---

## 🎨 3. Thiết kế Giao diện & Trải nghiệm Người dùng (UI/UX Specification)

Giao diện theo phong cách **Financial Intelligence Dashboard** (tối giản, sắc nét, hiện đại, tone màu Dark Slate / Indigo / Emerald):

### 3.1 Header & Status Bar (FR-11, FR-12)
- **Logo & Title:** `AICOR` — *AI Investment & Outcomes Comparative Analytics* (Phiên bản CMU SRS v5.1).
- **Live Stock MSFT Widget:** Giá hiện tại (USD) + Nhãn độ trễ: `⏱️ Yahoo Finance (trễ 15 phút)`.
- **System Sync Status:** Badge màu xanh `● Đồng bộ: Thành công` kèm thời gian sync gần nhất (`last_sync_utc`).
- **Nút "Phương pháp luận":** Mở Modal tóm tắt công thức và giới hạn phân tích.

### 3.2 Thẻ Tổng quan Công ty (Executive Metric Cards)
Hiển thị 3 thẻ tương ứng với 3 thực thể:
1. **Microsoft (MSFT)**:
   - Điểm $E$ quý gần nhất (`2026-Q2`).
   - Mức chi phí R&D quý gần nhất (USD).
   - Số lượng sản phẩm AI tích lũy.
2. **OpenAI**:
   - Điểm $E$ quý gần nhất.
   - Ước tính chi tiêu AI gần nhất + Mức độ tin cậy (`est_confidence`).
   - Số lượng sản phẩm ra mắt (Model mới nhóm A: GPT-4, GPT-4o, o1...).
3. **Anthropic**:
   - Điểm $E$ quý gần nhất.
   - Ước tính chi tiêu AI gần nhất + Mức độ tin cậy.
   - Số lượng sản phẩm ra mắt (Claude 3, Claude 3.5 Sonnet...).

### 3.3 Khu vực Biểu đồ Đa chiều (Interactive Chart Section - FR-06, FR-07)
Cung cấp thanh Tab chuyển đổi linh hoạt:
- **Tab 1: Biểu đồ Điểm Hiệu suất $E$ ($2022\text{-Q1} \to 2026\text{-Q2}$)**:
  - 3 đường tương ứng 3 công ty: Microsoft (Xanh dương), OpenAI (Xanh lá), Anthropic (Tím).
  - Trục ngang: 18 quý. Trục đứng: Điểm $E$.
  - Đường tham chiếu $E = 0$ (ngưỡng cân bằng tương đối).
  - Hover hiển thị Tooltip: $E$, $In$, $Out$, và sự kiện quan trọng trong quý đó nếu có.
- **Tab 2: Phân rã Đầu vào ($In$) & Đầu ra ($Out$)**:
  - Cho phép chọn xem từng công ty.
  - Hiển thị 2 đường $In$ (chuẩn hóa z-score) và $Out$ (chuẩn hóa z-score).
  - Minh họa trực quan khoảng cách $E = Out - In$.
- **Tab 3: Chỉ số Thành phần Thô**:
  - Đồ thị phụ hiển thị: Chi phí R&D/AI Spend thực tế, Product Score, Google Trends trung bình quý.

### 3.4 Dòng Thời gian Sự kiện (Timeline Events Overlay - FR-08)
- Danh sách 33 sự kiện sắp xếp theo ngày.
- Bộ lọc nhanh (Filter):
  - Tất cả (33)
  - 🚀 Ra mắt sản phẩm (`launch`: Category A / B / C)
  - 💰 Vòng gọi vốn (`funding`)
  - 🤝 Quan hệ hợp tác / Đối đầu (`relationship`: invest, partner, compete, statement)
- Mỗi sự kiện hiển thị: Ngày, Quý, Công ty, Tên sự kiện/Trích dẫn, Nguồn kiểm chứng (link ngoài).

### 3.5 Công cụ Phân bổ Danh mục Minh họa (Portfolio Simulator - FR-09, FR-10, UC-2)
- **3 Thanh trượt tỷ trọng:**
  - Microsoft: $w_{MSFT}$ (%)
  - OpenAI: $w_{OpenAI}$ (%)
  - Anthropic: $w_{Anthropic}$ (%)
  - **Cơ chế khóa tổng:** Tổng 3 thanh trượt luôn đảm bảo bằng $100\%$. Khi kéo 1 thanh trượt, 2 thanh trượt còn lại tự động tái phân bổ tỷ lệ thuận.
- **Bảng tính điểm danh mục:**
  - $\text{Score} = w_{MSFT} \times (-1.304) + w_{OpenAI} \times (-1.661) + w_{Anthropic} \times (-1.296)$ (lấy từ `portfolio_baseline.json`).
  - Hiển thị kết quả điểm danh mục tức thì.
- **CẢNH BÁO BẮT BUỘC (Disclaimer):**
  - Khung màu vàng/cam nổi bật với dòng chữ:
    > ⚠️ **Công cụ minh họa, không phải khuyến nghị đầu tư.**  
    > *Điểm danh mục dựa trên trung vị E của 4 quý gần nhất (2025-Q3 đến 2026-Q2). Điểm E là chỉ số hiệu suất tương đối so với lịch sử nội tại của từng công ty, không phản ánh tỷ suất sinh lời tài chính (ROI) thực tế.*

### 3.6 Chân trang (Footer - FR-11)
- Thông tin dự án: AICOR — CMU Foundations of Software Engineering (v5.1).
- Trạng thái đồng bộ dữ liệu: `Last sync: 2026-10-06T14:28:03Z | Status: Success | Quarters: 18 (2022-Q1 đến 2026-Q2)`.

---

## 🛠️ 4. Quy trình Thực hiện Từng Bước cho Muse Spark 1.3

1. **Khởi tạo project Frontend:**
   ```powershell
   # Tại thư mục gốc D:\Learning\DangHoc\DAFBE\7_Final
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   npm install
   npm install recharts lucide-react
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```
2. **Cấu hình sao chép dữ liệu tĩnh:**
   - Tạo thư mục `frontend/public/data/`.
   - Sao chép 4 file từ `data/processed/` sang `frontend/public/data/`:
     * `chart_series.json`
     * `timeline_events.json`
     * `portfolio_baseline.json`
     * `manifest.json`
   - Thêm script nhỏ trong `package.json` để tự động copy dữ liệu trước mỗi lần build:
     `"prebuild": "node -e \"const fs=require('fs'); fs.cpSync('../data/processed', './public/data', {recursive:true, filter:(src)=>src.endsWith('.json')})\""`
3. **Triển khai Data Service (`src/services/dataService.ts`):**
   - Đọc trực tiếp `/data/chart_series.json`, `/data/timeline_events.json`, `/data/portfolio_baseline.json`, `/data/manifest.json`.
   - Có cơ chế fallback: Thử gọi `http://localhost:8000/api/stock/msft/live` để lấy giá mới nhất, nếu không được thì đọc fallback từ dữ liệu tĩnh.
4. **Viết các Components theo giao diện đã thiết kế.**
5. **Kiểm tra và Build:**
   - Chạy `npm run build` để kiểm tra TypeScript compilation và Vite production build hoàn toàn sạch lỗi.
   - Chạy `npm run dev` để kiểm tra giao diện hiển thị đúng trên trình duyệt.
6. **Cập nhật tài liệu bộ nhớ dự án:**
   - Cập nhật `.ai/TASKS.md` (chuyển AICOR-020 sang DONE).
   - Cập nhật `.ai/PROJECT_STATE.md`, `.ai/HANDOFF.md`, `.ai/CHANGELOG.md`.
