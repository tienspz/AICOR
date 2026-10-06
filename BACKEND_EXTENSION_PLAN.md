# Kế hoạch Hoàn thiện & Mở rộng Backend AICOR (CMU SRS v5.1)
*(Tài liệu chi tiết & Prompt mẫu để giao việc cho Agent OpenCode và Freebuff)*

**Mã dự án:** AICOR  
**Đặc tả tham chiếu:** [PROJECT_SPEC_CMU.md](PROJECT_SPEC_CMU.md) (CMU SRS v5.1)  
**Tình trạng hiện tại của Backend:**
- ✅ **Lớp 1 (Collection)**: Đã có 4 collector (`collector_edgar`, `collector_stock`, `collector_trends`, `collector_events`), hệ thống chống ban IP & RateLimiter (`resilience.py`), bộ lưu trữ append-only khử trùng lặp (`storage.py`).
- ✅ **Lớp 2 (Cleaning & Computation)**: Đã có bộ làm sạch & chấm điểm rubric A/B/C (`cleaner.py`), tính MA 4Q (`aggregator.py`), tính Z-score riêng theo từng công ty với chốt an toàn $\sigma=0$ (`calculator.py`), phân tích độ nhạy 3 bộ trọng số (`sensitivity.py`), xuất dữ liệu 3 tầng (`raw/`, `cleaned/`, `processed/fact_quarterly.csv`).
- ✅ **Tự động hóa Cloud**: GitHub Actions workflows (`fast_rhythm.yml` 6h/lần, `slow_rhythm.yml` 24h/lần) đã test thành công trên cloud.

---

## 📌 1. Phân tích: Backend Còn Thiếu Gì Đối Chiếu với SRS v5.1?

Mặc dù luồng crawl và tính toán dữ liệu bằng CSV đã hoàn chỉnh, để đáp ứng 100% các tiêu chí học thuật và kỹ thuật của đồ án chuẩn CMU, Backend còn **5 hạng mục cần bổ sung**:

```
                                  [ AICOR DATA FLOW ]
                                           │
 ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
 │                                                                                   │
 ▼                                                                                   ▼
[ NGUỒN CRAWL TỰ ĐỘNG MỞ RỘNG ]                                    [ TẦNG LƯU TRỮ & PHỤC VỤ ]
 1. Blog RSS / HTML Scrapers (OpenAI, Anthropic, MSFT) [BE-02]       4. SQLite DDL Engine & CSV Sync [BE-01]
 2. SEC EDGAR 10-Q Filing Monitor & Alert [BE-03]                   5. Pre-computed JSON Bundles [BE-04]
                                                                     6. FastAPI REST Service & Live Stock [BE-05]
```

| Mã Task | Hạng mục còn thiếu | Mục tiêu theo CMU SRS | Mức độ ưu tiên | Phù hợp Agent |
| :---: | :--- | :--- | :---: | :---: |
| **BE-01** | **SQLite Database Engine & CSV Sync** | Mục 2.1 & 3.4: Lưu trữ song song vào SQLite (`aicor.db`), hỗ trợ truy vấn SQL quan hệ chuẩn hóa. | **P0** (Bắt buộc) | **OpenCode** |
| **BE-04** | **Pre-computed Web JSON Bundles** | FR-14 & NFR-01: Xuất JSON tĩnh tối ưu cho biểu đồ, sự kiện, baseline danh mục để Web tải < 3s. | **P0** (Bắt buộc) | **OpenCode** |
| **BE-02** | **RSS / Blog Scrapers Tự Động** | IF-4 & Phụ lục A: Tự động phát hiện bài đăng mới của OpenAI, Anthropic, MSFT và gắn tag A/B/C. | **P1** (Quan trọng) | **Freebuff** |
| **BE-03** | **SEC EDGAR 10-Q Filing Monitor** | FR-03: Tự động quét Atom feed của SEC để nhận diện ngay khi Microsoft nộp báo cáo 10-Q mới. | **P1** (Quan trọng) | **Freebuff** |
| **BE-05** | **FastAPI Service & Live Stock Widget** | FR-12: REST API phục vụ fullstack, cung cấp endpoint giá cổ phiếu MSFT cập nhật theo phút. | **P2** (Mở rộng) | **OpenCode / Freebuff** |

---

## 📋 2. Đặc tả Chi tiết Từng Task Kỹ thuật

---

### 🔹 Task BE-01: SQLite Database Engine & Đồng bộ CSV sang SQLite (P0)

- **Mục tiêu**: Hiện tại dữ liệu đang lưu trong CSV. Cần xây dựng engine SQLite tạo cơ sở dữ liệu `data/processed/aicor.db` gồm 6 bảng theo đúng Mục 3.4 CMU SRS và hàm đồng bộ dữ liệu từ CSV sang SQLite.
- **Tệp cần tạo / sửa**:
  - `src/computation/db.py` (Mới)
  - `src/computation/pipeline.py` (Cập nhật gọi hàm sync ở bước cuối)
  - `tests/test_db.py` (Mới)
- **Đặc tả Schema DDL SQL**:
  ```sql
  -- 1. dim_company
  CREATE TABLE IF NOT EXISTS dim_company (
      company_id INTEGER PRIMARY KEY,
      name TEXT NOT NULL UNIQUE,
      ticker TEXT
  );

  -- 2. fact_quarterly
  CREATE TABLE IF NOT EXISTS fact_quarterly (
      company_id INTEGER NOT NULL,
      quarter TEXT NOT NULL,
      rnd_spend REAL,
      ai_spend_est REAL,
      est_confidence TEXT CHECK(est_confidence IN ('high', 'medium', 'low', NULL)),
      trends_qavg REAL,
      product_score REAL,
      product_ma4q REAL,
      trends_ma4q REAL,
      in_score REAL,
      out_score REAL,
      e_score REAL,
      valid_from DATE NOT NULL,
      PRIMARY KEY (company_id, quarter),
      FOREIGN KEY (company_id) REFERENCES dim_company(company_id)
  );

  -- 3. event_launch
  CREATE TABLE IF NOT EXISTS event_launch (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company_id INTEGER NOT NULL,
      launch_date DATE NOT NULL,
      quarter TEXT NOT NULL,
      product_name TEXT NOT NULL,
      category TEXT CHECK(category IN ('A', 'B', 'C')),
      points REAL NOT NULL,
      source_url TEXT NOT NULL,
      coder TEXT NOT NULL,
      FOREIGN KEY (company_id) REFERENCES dim_company(company_id)
  );

  -- 4. event_funding
  CREATE TABLE IF NOT EXISTS event_funding (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company_id INTEGER NOT NULL,
      funding_date DATE NOT NULL,
      quarter TEXT NOT NULL,
      amount REAL NOT NULL,
      valuation REAL,
      source_url TEXT NOT NULL,
      FOREIGN KEY (company_id) REFERENCES dim_company(company_id)
  );

  -- 5. event_relationship
  CREATE TABLE IF NOT EXISTS event_relationship (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_date DATE NOT NULL,
      quarter TEXT NOT NULL,
      parties TEXT NOT NULL,
      rel_type TEXT NOT NULL,
      quote TEXT,
      source_url TEXT NOT NULL
  );

  -- 6. sync_log
  CREATE TABLE IF NOT EXISTS sync_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_at TIMESTAMP NOT NULL,
      rhythm TEXT NOT NULL,
      status TEXT NOT NULL,
      rows_added INTEGER DEFAULT 0,
      error TEXT
  );
  ```
- **Hàm cần viết trong `src/computation/db.py`**:
  1. `init_database(db_path: Optional[Path] = None) -> sqlite3.Connection`: Khởi tạo bảng nếu chưa có.
  2. `populate_dim_companies(conn: sqlite3.Connection) -> None`: Nạp 3 công ty cố định (1: Microsoft - MSFT, 2: OpenAI - None, 3: Anthropic - None).
  3. `sync_csv_to_sqlite(db_path: Optional[Path] = None) -> Dict[str, int]`: Đọc toàn bộ các file `data/cleaned/*.csv` và `data/processed/fact_quarterly.csv` rồi INSERT OR REPLACE vào các bảng tương ứng. Trả về số dòng nạp được của từng bảng.
- **Tiêu chuẩn nghiệm thu**:
  - Chạy `pytest tests/test_db.py` thành công.
  - Sau khi chạy `python run_pipeline.py --mode compute`, tệp `data/processed/aicor.db` được tạo ra và có đủ dữ liệu 54 dòng `fact_quarterly`.

---

### 🔹 Task BE-04: Bộ Xuất JSON Tĩnh Chuẩn Hóa cho Frontend (P0)

- **Mục tiêu**: Tuân thủ **FR-14** (*Web React chỉ đọc dữ liệu đã tính toán, không tự tính lại E*) và **NFR-01** (*Tải trang nhanh dưới 3 giây*). Frontend React không cần phân tích chuỗi CSV mà có thể import trực tiếp các file JSON cấu trúc sẵn.
- **Tệp cần tạo / sửa**:
  - `src/computation/exporter.py` (Mới)
  - `src/computation/pipeline.py` (Gọi exporter ở bước cuối)
  - `tests/test_exporter.py` (Mới)
- **Cấu trúc 3 tệp JSON cần xuất vào `data/processed/`**:
  1. `chart_series.json`:
     ```json
     {
       "generated_at": "2026-10-06T...",
       "quarters": ["2022-Q1", "2022-Q2", "...", "2026-Q2"],
       "companies": {
         "MSFT": {
           "company_id": 1,
           "name": "Microsoft",
           "series": [
             { "quarter": "2022-Q1", "in_score": 0.12, "out_score": 0.45, "e_score": 0.33, "rnd_spend": 6.5, "trends_qavg": 42.1 }
           ]
         },
         "OpenAI": { ... },
         "Anthropic": { ... }
       }
     }
     ```
  2. `timeline_events.json`:
     Danh sách hợp nhất toàn bộ sự kiện ra mắt sản phẩm, gọi vốn và quan hệ ba bên, sắp xếp theo thứ tự thời gian tăng dần, gắn kèm cờ `quarter` và `category` để giao diện dễ dàng phủ lên trục hoành của đồ thị (FR-06, FR-08).
  3. `portfolio_baseline.json`:
     Giá trị trung vị $E$ 4 quý gần nhất của từng công ty:
     ```json
     {
       "reference_window": ["2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"],
       "medians": {
         "MSFT": 0.41,
         "OpenAI": 0.85,
         "Anthropic": 0.62
       },
       "disclaimer": "Công cụ minh họa, không phải khuyến nghị đầu tư."
     }
     ```
- **Tiêu chuẩn nghiệm thu**:
  - Chạy `python run_pipeline.py --mode compute` tạo ra 3 tệp JSON đúng cấu trúc.
  - Viết test trong `tests/test_exporter.py` xác minh cấu trúc khóa JSON và không có giá trị `NaN` (thay bằng `null`).

---

### 🔹 Task BE-02: Bộ Scraper Tự Động Quét RSS/Blog của OpenAI, Anthropic, Microsoft (P1)

- **Mục tiêu**: Tự động phát hiện bài đăng mới về sản phẩm/tính năng (IF-4, Phụ lục A) thay vì phụ thuộc thủ công vào seed.
- **Tệp cần tạo / sửa**:
  - `src/collection/scrapers/__init__.py`
  - `src/collection/scrapers/blog_scraper.py`
  - `tests/test_scrapers.py`
- **Nguồn cần cào**:
  1. **OpenAI**: Feed RSS `https://openai.com/news/rss.xml` hoặc changelog chính thức.
  2. **Anthropic**: Bóc tách bài đăng từ `https://www.anthropic.com/news`.
  3. **Microsoft AI**: Feed RSS `https://blogs.microsoft.com/feed/` (lọc từ khóa AI/Copilot).
- **Bộ lọc từ khóa tự động gán Nhóm A/B/C (Phụ lục A)**:
  - **Nhóm A (3 điểm)**: Tiêu đề chứa "technical report", "introducing [model]", "new model", "frontier", "gpt-5", "claude 4".
  - **Nhóm B (2 điểm)**: Tiêu đề chứa "api", "preview", "enterprise", "turbo", "fine-tuning", "claude 3.5", "o1-mini".
  - **Nhóm C (1 điểm)**: Tiêu đề chứa "update", "feature", "integration", "app", "plugin", "availability".
- **Lưu trữ**:
  - Ghi các sự kiện phát hiện mới vào `data/raw/events_launch_raw.csv` qua `storage.append_to_raw_csv()`. Tự động khử trùng lặp qua `source_url`.
  - Tuân thủ `resilience.py` để không gửi quá nhiều request liên tiếp.
- **Tiêu chuẩn nghiệm thu**:
  - Test mock XML feed trả về danh sách event chuẩn định dạng schema `events_launch_raw`.

---

### 🔹 Task BE-03: SEC EDGAR 10-Q Filing Monitor & Auto-Sync (P1)

- **Mục tiêu**: Đáp ứng yêu cầu **FR-03**: *"Hệ thống phải phát hiện 10-Q mới của Microsoft trên EDGAR và đồng bộ chi phí R&D"*.
- **Tệp cần tạo / sửa**:
  - `src/collection/edgar_monitor.py`
  - `.github/workflows/edgar_sync.yml`
- **Mô tả công việc**:
  1. Gọi SEC Atom Feed:
     `https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=0000789019&type=10-Q&output=atom`
     với header User-Agent hợp lệ (`AICOR Research contact@aicor-research.edu`).
  2. Kiểm tra ngày filing gần nhất. Nếu ngày filing lớn hơn ngày bản ghi mới nhất trong `data/raw/rnd_msft_raw.csv`:
     - Tự động gọi `collector_edgar.run_edgar_collector()` để trích xuất mục Research and Development.
     - Tự động chạy lại `cleaner` và `pipeline` để cập nhật $E$-score.
     - Ghi nhận `rhythm: edgar`, `status: success` vào `sync_log.csv`.
  3. Tạo workflow GitHub Actions `.github/workflows/edgar_sync.yml` chạy hàng tuần (ví dụ thứ 2 lúc 00:00 UTC) hoặc khi bấm Run workflow thủ công.
- **Tiêu chuẩn nghiệm thu**:
  - Hàm `check_new_filings()` chạy an toàn, trả về boolean xem có filing mới hay không.

---

### 🔹 Task BE-05: Dịch vụ REST API Nhẹ (FastAPI) & Live MSFT Stock Widget (P2)

- **Mục tiêu**: Cung cấp API phục vụ Web App khi chạy local hoặc fullstack, đồng thời hỗ trợ **FR-12**: *"gọi API giá cổ phiếu mỗi phút khi trang đang mở và hiển thị độ trễ"*.
- **Tệp cần tạo / sửa**:
  - `src/api/__init__.py`
  - `src/api/main.py`
  - `src/api/routes.py`
  - `requirements.txt` (thêm `fastapi`, `uvicorn`)
  - `tests/test_api.py`
- **Endpoints cần có**:
  - `GET /api/health`: Trả về trạng thái hệ thống, manifest, thời điểm sync gần nhất.
  - `GET /api/facts`: Dữ liệu bảng `fact_quarterly` (cho phép lọc `?company_id=1&quarter=2024-Q1`).
  - `GET /api/events`: Danh sách các sự kiện dòng thời gian.
  - `GET /api/sensitivity`: Dữ liệu phân tích độ nhạy 3 bộ trọng số.
  - `GET /api/stock/msft/live`: Gọi `yfinance` lấy giá hiện tại của MSFT, trả về:
    `{"symbol": "MSFT", "price": 450.2, "currency": "USD", "latency_minutes": 15, "source": "Yahoo Finance (delayed 15m)"}`
  - `POST /api/simulate-portfolio`: Nhận JSON `{"weights": {"MSFT": 0.4, "OpenAI": 0.4, "Anthropic": 0.2}}`.
    Kiểm tra tổng trọng số = 1.0 (sai số $\le 0.001$). Tính điểm danh mục = $\sum w_c \times \text{Median}(E_c, 4Q)$.
  - Cấu hình CORS Middleware (`allow_origins=["*"]`) để frontend React không bị chặn.
- **Tiêu chuẩn nghiệm thu**:
  - Viết test với `fastapi.testclient.TestClient` trong `tests/test_api.py`.

---

## 🤖 3. Các Prompt Mẫu Sẵn Sàng Copy-Paste Cho Từng Agent

### 📌 Prompt 1: Dành cho OpenCode (Triển khai Task BE-01 và BE-04)

```markdown
Chào OpenCode! Hãy giúp tôi triển khai 2 task Backend P0 cho dự án AICOR:
1. Task BE-01: SQLite Database Engine & CSV Sync
   - Tạo file `src/computation/db.py` gồm:
     + Hàm `init_database(db_path)` tạo 6 bảng SQLite chuẩn theo Mục 3.4 CMU SRS (`dim_company`, `fact_quarterly`, `event_launch`, `event_funding`, `event_relationship`, `sync_log`).
     + Hàm `populate_dim_companies(conn)` chèn 3 công ty (Microsoft ID 1, OpenAI ID 2, Anthropic ID 3).
     + Hàm `sync_csv_to_sqlite(db_path)` đọc dữ liệu từ `data/cleaned/*.csv` và `data/processed/fact_quarterly.csv` rồi INSERT OR REPLACE vào SQLite (`data/processed/aicor.db`).
   - Tích hợp gọi `sync_csv_to_sqlite()` vào bước cuối của `run_computation_pipeline()` trong `src/computation/pipeline.py`.
   - Viết bài test trong `tests/test_db.py`.

2. Task BE-04: Pre-computed Web JSON Bundles
   - Tạo file `src/computation/exporter.py` gồm hàm `export_web_json_bundles()`:
     + Xuất `data/processed/chart_series.json` (cấu trúc series theo từng công ty để React dễ vẽ biểu đồ).
     + Xuất `data/processed/timeline_events.json` (gộp toàn bộ sự kiện sắp xếp theo ngày).
     + Xuất `data/processed/portfolio_baseline.json` (chứa trung vị E của 4 quý gần nhất cho MSFT, OpenAI, Anthropic để phục vụ thanh trượt phân bổ vốn FR-10).
   - Tích hợp gọi `export_web_json_bundles()` vào `src/computation/pipeline.py`.
   - Viết test trong `tests/test_exporter.py`.

Lưu ý:
- Tuân thủ nghiêm ngặt PROJECT_SPEC_CMU.md: E = Out - In là chênh lệch kết quả, không phải ROI. Không sửa đổi logic toán học đã hoàn chỉnh.
- Chạy `pytest` kiểm tra toàn bộ test phải pass.
```

---

### 📌 Prompt 2: Dành cho Freebuff (Triển khai Task BE-02 và BE-03)

```markdown
Chào Freebuff! Hãy giúp tôi hoàn thiện 2 task Backend về cào dữ liệu và giám sát tự động cho dự án AICOR:
1. Task BE-02: RSS & Official Blog Scraper
   - Tạo module `src/collection/scrapers/blog_scraper.py` để quét bài viết mới từ:
     + OpenAI RSS: `https://openai.com/news/rss.xml`
     + Anthropic News: `https://www.anthropic.com/news`
     + Microsoft Official Blog: `https://blogs.microsoft.com/feed/`
   - Áp dụng rubric từ khóa theo Phụ lục A của PROJECT_SPEC_CMU.md để phân loại sơ bộ:
     + Nhóm A (3 điểm): "technical report", "introducing", "new model"
     + Nhóm B (2 điểm): "api", "preview", "enterprise", "turbo"
     + Nhóm C (1 điểm): "update", "feature", "integration"
   - Ghi bài viết mới vào `data/raw/events_launch_raw.csv` qua `src/collection/storage.py` (append-only, khử trùng lặp qua URL).
   - Sử dụng `resilience.py` để rate limit và retry.
   - Viết test mock trong `tests/test_scrapers.py`.

2. Task BE-03: SEC EDGAR 10-Q Filing Monitor & Alert
   - Tạo file `src/collection/edgar_monitor.py` kiểm tra Atom feed của SEC EDGAR:
     `https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=0000789019&type=10-Q&output=atom`
   - Nếu phát hiện 10-Q mới hơn bản ghi cuối cùng trong `data/raw/rnd_msft_raw.csv`:
     + Tự động kích hoạt cào R&D và gọi pipeline tính lại E-score.
     + Ghi log vào `sync_log.csv` (rhythm: edgar).
   - Tạo GitHub Actions workflow `.github/workflows/edgar_sync.yml` lập lịch kiểm tra hàng tuần.

Lưu ý:
- Giữ nguyên tắc dữ liệu Raw là Append-Only, không ghi đè làm mất lịch sử cũ.
- Chạy `pytest` đảm bảo code sạch và chạy tốt.
```

---

### 📌 Prompt 3: Dành cho OpenCode / Freebuff (Triển khai Task BE-05)

```markdown
Chào bạn! Hãy giúp tôi triển khai Task BE-05: Xây dựng REST API Service bằng FastAPI cho AICOR:
1. Thêm `fastapi>=0.110.0` và `uvicorn>=0.28.0` vào `requirements.txt`.
2. Tạo `src/api/main.py` và `src/api/routes.py`:
   - Endpoint `GET /api/health`: Trả về trạng thái manifest và dữ liệu đồng bộ.
   - Endpoint `GET /api/facts`: Trả về danh sách fact_quarterly (hỗ trợ query param `company_id`, `quarter`).
   - Endpoint `GET /api/events`: Trả về sự kiện timeline từ database/CSV.
   - Endpoint `GET /api/sensitivity`: Trả về kết quả phân tích 3 bộ trọng số.
   - Endpoint `GET /api/stock/msft/live`: Gọi `yfinance` lấy giá cổ phiếu MSFT mới nhất, kèm nhãn `latency_minutes: 15` theo yêu cầu FR-12.
   - Endpoint `POST /api/simulate-portfolio`: Nhận 3 trọng số w_1, w_2, w_3, kiểm tra tổng = 1.0, tính điểm danh mục = sum(w * median(E_4Q)).
   - Kích hoạt CORS Middleware cho phép mọi domain (đặc biệt là localhost Vite frontend).
3. Viết kiểm thử tự động trong `tests/test_api.py` sử dụng `fastapi.testclient.TestClient`.
4. Đảm bảo chạy `pytest` vượt qua tất cả các bài kiểm tra.
```

---

## 🚦 4. Thứ tự Thực hiện Đề xuất (Execution Sequence)

| Bước | Agent | Task | Trọng tâm |
| :---: | :---: | :---: | :--- |
| **1** | **OpenCode** | **BE-01 & BE-04** | Hoàn thành SQLite Engine & xuất sẵn JSON Bundles (để Web React có thể dùng ngay). |
| **2** | **Freebuff** | **BE-02 & BE-03** | Mở rộng cào tự động Blog RSS và giám sát SEC 10-Q cho Microsoft. |
| **3** | **OpenCode / Freebuff** | **BE-05** | Xây dựng FastAPI service phục vụ live stock widget và simulator. |

---

*Tài liệu này được biên soạn đầy đủ và chuẩn hóa theo CMU SRS v5.1. Bạn có thể copy trực tiếp từng Prompt trên đưa cho OpenCode hoặc Freebuff thực hiện mà không cần giải thích thêm.*
