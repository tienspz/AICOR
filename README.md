# ĐV-ĐR — Hệ thống Nghiên cứu Đầu vào – Đầu ra AI

> **Tên hệ thống:** Hệ thống Nghiên cứu Đầu vào – Đầu ra AI, viết tắt **ĐV-ĐR** (AI Input–Output Research System).
> **Định danh kỹ thuật giữ nguyên:** Python package, `config_version` (`aicor-analysis-v1`), `model_id`, User-Agent `AICOR-research/1.0`, biến `AICOR_DATA_DIR` và đường dẫn repo GitHub vẫn dùng slug `aicor` để các artifact đã publish còn tái lập và kiểm tra được checksum.

> **Đề tài:** *Phân tích hiệu suất đầu tư AI và kết quả của Microsoft, Alphabet theo quý từ 2022 đến nay*
> *(Analysis of AI Investment Efficiency and Outcomes of Microsoft and Alphabet on a Quarterly Basis from 2022 to Present)*

[![Validate](https://github.com/tienspz/AICOR/actions/workflows/validate.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/validate.yml)
[![Crawl SEC](https://github.com/tienspz/AICOR/actions/workflows/crawl-sec.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/crawl-sec.yml)
[![Crawl Market](https://github.com/tienspz/AICOR/actions/workflows/crawl-market.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/crawl-market.yml)
[![Crawl Trends](https://github.com/tienspz/AICOR/actions/workflows/crawl-trends.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/crawl-trends.yml)
[![Crawl IR](https://github.com/tienspz/AICOR/actions/workflows/crawl-ir.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/crawl-ir.yml)

Hệ thống thu thập dữ liệu định lượng, tiền xử lý và so sánh mức đầu vào liên quan đến AI ($In$) với các chỉ báo đầu ra AI ($Out$) theo quý giữa **Microsoft Corporation (MSFT)** và **Alphabet Inc. (GOOGL)**.

Kết quả đo lường là điểm tương đối:

$$E = Out - In$$

> **Lưu ý liêm chính nghiên cứu:** Điểm $E$ là thước đo tương đối để quan sát xu hướng lịch sử và kiểm tra độ nhạy trọng số; không phải ROI, lợi nhuận hay bằng chứng quan hệ nhân quả (SRS §1.1).
>
> **Lớp dự báo ĐV-ĐR (Phase 2.5):** Bổ sung nowcast quý hiện tại ($h=0$) trước khi có 10-Q và forecast 1 quý tới ($h=1$) bằng mô hình tuyến tính có kiểm soát (Ridge/Elastic Net) kèm khoảng tin cậy 80%/95%, cảnh báo rủi ro (alert) và giải thích yếu tố đóng góp (driver attribution); tất cả được gắn nhãn thử nghiệm (experimental) và không phải khuyến nghị đầu tư (SRS §0 Quyết định 5, §7.6).

---

## 1. Kiến trúc hệ thống

Dự án tuân thủ nghiêm ngặt quy trình tiền xử lý 9 thao tác của **Lecture 07 (Data Preprocessing)** và SRS Baseline ([SPEC.md](SPEC.md)):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA COLLECTION (Tiered)                        │
│  SEC EDGAR (Tier S)   Yahoo Finance (Tier B)  Trends (Tier B)  IR (A)  │
│      [≤10 req/s]         [MSFT, GOOGL]         [Circuit-Break] [Rubric]│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Append-only + SHA-256 + sync_log
┌───────────────────────────────────▼────────────────────────────────────┐
│                  PREPROCESSING PIPELINE (Lecture 07)                   │
│  1. Cleaning      : Strip text, ép numeric, lọc dòng rác                │
│  2. Missing       : NULL policy, status unavailable, ghi reason        │
│  3. Transform     : YTD→Quarter (Q4=FY-9M), align calendar (DAT-01)    │
│  4. Integrate     : Join panel, company dummy is_msft, product score   │
│  5. Scale/Norm    : Rolling z-score 16Q (std=0 guard), MA4Q (min 4Q)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Analysis-ready panel
┌───────────────────────────────────▼────────────────────────────────────┐
│       METRIC & NOWCAST/FORECAST ENGINE (Phase 2 & Phase 2.5)           │
│  - Metrics        : In = z(RD), Out = w1*z(Product) + w2*z(Trends), E  │
│  - Dự báo ĐV-ĐR   : Nowcast (h=0), Forecast (h=1) qua Ridge/ElasticNet │
│  - Assurance      : 80%/95% Interval, Point-in-time guard, Top 3 Driver│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Validated artifacts
┌───────────────────────────────────▼────────────────────────────────────┐
│         AUTOMATION & 7-VIEW DASHBOARD (Phase 3 - GitHub Pages)         │
│  - 4 Cron Crawlers + Quality Gates tự động trên GitHub CI              │
│  - Dashboard 7 Chế độ xem: DSH-01 đến DSH-07 (Lớp dự báo & Alerts)     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Nguồn dữ liệu & Lịch thu thập tự động (Rate Limit & Schedules)

Các crawler hoạt động độc lập (NFR-04: một nguồn lỗi không làm ảnh hưởng nguồn khác), lưu bản snapshot nguyên gốc cùng mã hash SHA-256 trong `data/raw/manifest.csv` và ghi nhật ký vào `data/sync_log.jsonl`.

| Nguồn | Tier | URL Canonical | Chu kỳ tự động (GitHub Actions) | Rate Limit / Cơ chế an toàn |
| :--- | :---: | :--- | :--- | :--- |
| **SEC EDGAR XBRL** | **Tier S** | `data.sec.gov/api/xbrl/companyfacts/` | `0 */6 * * *` (Mỗi 6 tiếng) | `REQUEST_DELAY = 0.1s` (≤ 10 req/s, NFR-07); khai báo User-Agent; Tag resolver linh hoạt theo kỳ |
| **Market Data** | **Tier B** | Yahoo Finance (`yfinance`) | `0 13-20 * * 1-5` (Sau phiên giao dịch) | Giữ nguyên `adj_close` và `volume`, lưu CSV định kỳ (SRC-09) |
| **Google Trends** | **Tier B** | Google Trends (`pytrends`) | `0 */12 * * *` (Mỗi 12 tiếng) | Circuit-breaker tự động fallback `TrendsUnavailable` (§7.4) |
| **IR & Product Blogs** | **Tier A** | Microsoft, Azure, MS Research, Google, Cloud & Research Blogs (6 feeds) | `0 2 * * *` (Hằng ngày lúc 02:00 UTC) | Chuẩn hóa URL, dedup bài viết đa kênh (title+date), polite delay 2.0s/feed, phân loại A/B/C theo rubric |

---

## 3. Cấu trúc thư mục

```text
├── .github/workflows/          # CI, 4 crawler schedules, pipeline và GitHub Pages
│   ├── validate.yml            # Chạy test suite & data quality gates trên push/PR
│   ├── crawl-sec.yml           # Cron crawl SEC XBRL (Tier S) + auto-preprocess
│   ├── crawl-market.yml        # Cron crawl Yahoo Finance (Tier B) + auto-preprocess
│   ├── crawl-trends.yml        # Cron crawl Google Trends (Tier B) + auto-preprocess
│   ├── crawl-ir.yml            # Cron crawl IR Blogs (Tier A) + auto-preprocess
│   ├── pipeline.yml            # Lịch chạy pipeline phân tích
│   └── pages.yml               # Deploy dashboard lên GitHub Pages
├── config/analysis.yaml        # Cấu hình có phiên bản cho metric engine và forecast
├── data/
│   ├── raw/                    # Snapshot dữ liệu nguồn và manifest SHA-256
│   ├── processed/              # Bảng chuẩn hóa, kết quả phân tích và forecast
│   ├── quality/                # Báo cáo kiểm tra chất lượng
│   ├── logs/                   # Log vận hành
│   └── sync_log.jsonl          # Nhật ký đồng bộ crawler
├── scripts/                    # Tiện ích đồng bộ portable Vibe Code skills
├── src/aicor/                  # Mã nguồn chính của hệ thống
│   ├── sources/                # Crawler SEC, market, Trends và IR
│   ├── preprocess/             # Tiền xử lý dữ liệu nguồn
│   ├── compute/                # Tính features và In/Out/E
│   ├── forecast/               # Lớp dự báo, backtest, alert và model card
│   └── pipeline/               # CLI, điều phối, artifacts và dashboard publish
├── tests/                      # Unit, contract và integration tests
├── web/                        # Dashboard tĩnh, không cần bước build frontend
│   ├── index.html
│   ├── assets/
│   └── data/                   # Manifest và payload dashboard đã publish
├── pyproject.toml              # Cấu hình dự án Python & dependencies
└── SPEC.md                     # Đặc tả yêu cầu hệ thống SRS Baseline
```

---

## 4. Cài đặt & Sử dụng

### 4.1 Yêu cầu môi trường
- Python `>= 3.12`
- Trình quản lý gói [`uv`](https://github.com/astral-sh/uv)

### 4.2 Chạy demo dashboard (dùng dữ liệu đã publish)

Demo dashboard tĩnh dùng dữ liệu trong `web/data/`; không cần cài dependencies Python,
API key hay chạy crawler. Từ thư mục gốc repo, mở PowerShell:

```powershell
python --version
python -m http.server 8765 --directory web
```

Mở <http://localhost:8765> trong trình duyệt. Giữ cửa sổ terminal đang chạy server;
nhấn `Ctrl+C` để dừng. Không mở `web/index.html` trực tiếp bằng `file://`, vì dashboard
cần HTTP để tải manifest và payload dữ liệu.

Để deploy dashboard lên Vercel, giữ **Root Directory** là thư mục gốc repo và đặt
**Framework Preset** thành **Other**. Cấu hình trong `vercel.json` sẽ publish trực tiếp
thư mục `web/`; không cần Python entrypoint hay bước build.

### 4.3 Cài đặt dependencies
```bash
git clone https://github.com/tienspz/AICOR.git
cd AICOR

# Đồng bộ dependencies và cài project
uv sync --all-extras
```

### 4.4 Chạy bộ kiểm thử
```bash
# Chạy test suite
uv run python -m pytest -v

# Chạy kèm báo cáo độ phủ mã nguồn (coverage)
uv run python -m pytest --cov=src/aicor tests/
```

### 4.5 Chạy crawler độc lập thủ công
Các lệnh crawler cần kết nối mạng. SEC EDGAR yêu cầu khai báo `SEC_USER_AGENT`
trong file `.env` (xem `.env.example`).

```bash
# Crawl báo cáo tài chính SEC XBRL
uv run python -m aicor.sources.sec

# Crawl giá cổ phiếu thị trường
uv run python -m aicor.sources.market

# Crawl dữ liệu Google Trends
uv run python -m aicor.sources.trends

# Crawl sản phẩm và sự kiện IR blogs
uv run python -m aicor.sources.ir
```

### 4.6 Chạy pipeline
```bash
# Chỉ thu thập dữ liệu (gọi các crawler; cần mạng)
uv run python -m aicor.pipeline.run --stage collect

# Tiền xử lý dữ liệu đã có trong data/raw/
uv run python -m aicor.pipeline.run --stage preprocess

# Tính metrics/forecast và publish dữ liệu cho dashboard
uv run python -m aicor.pipeline.run --stage analysis

# Chạy preprocess rồi analysis; không tự chạy crawler
uv run python -m aicor.pipeline.run --stage all
```

---

## 5. Nguyên tắc thiết kế cốt lõi (NFRs)

- **NFR-01 (Tính tái lập):** Snapshot nguồn lưu mã băm SHA-256 trong `data/raw/manifest.csv`; artifact phân tích và dashboard cũng có manifest/checksum riêng.
- **NFR-02 (Tính truy vết):** Mọi dòng dữ liệu phân tích đều có `source_id` dẫn về tài liệu gốc của công ty.
- **NFR-03 (Quản lý phiên bản cấu hình):** Tham số metric và forecast nằm trong `config/analysis.yaml`.
- **NFR-04 (Khả năng chịu lỗi):** Lỗi ở 1 nguồn (ví dụ Google Trends chặn IP) sẽ chuyển trạng thái sang `partial`, bảo toàn toàn bộ dữ liệu SEC/IR mà không bị rollback.
- **NFR-06 (Bảo mật):** Không hardcode API key/secret. User-Agent lấy từ biến môi trường `SEC_USER_AGENT`.
- **NFR-07 (Tuân thủ nguồn):** Tuân thủ giới hạn SEC `≤ 10 req/s` bằng bộ điều phối thời gian cố định; IR blogs áp dụng polite fetch (delay 2.0s/feed kèm khai báo User-Agent đầy đủ).

---

## 6. Lộ trình phát triển tiếp theo

- [x] **Phase 1: Data Collection & Preprocessing** (Crawlers, preprocessing và quality gates).
  - Tầng raw bất biến (SEC facts XBRL, Market 1,255 bars, Trends 1,004 rows, IR 204 products).
  - Tầng processed chuẩn hóa: 5 bảng CSV tại `data/processed/` (44 quý từ 2021-Q1 đến 2026-Q2).
  - Khắc phục triệt để logic cross-tag Q4 cho GOOGL: $Q_4 = FY - 9M$, cân đối $|Assets - (Liabilities + Equity)| = 0.0$.
  - Tự động hóa khép kín: Tự động crawl, tiền xử lý, kiểm tra chất lượng và commit/push trên GitHub Actions.
- [x] **Phase 2: Metric Computation Engine ($In$, $Out$, $E$)** — hoàn thành (xem §7)
  - Tính toán $In = z(\text{RD})$ (với RD là chi phí R&D) đối xứng cho 2 công ty.
  - Tính toán $Out = w_1 \cdot z(\text{Product MA4Q}) + w_2 \cdot z(\text{Trends MA4Q})$ với 3 kịch bản trọng số độ nhạy ($0.6/0.4, 0.5/0.5, 0.7/0.3$).
  - Xử lý các case ngoại lệ: $std = 0 \to \text{degenerate}$, $< 4$ quý $\to \text{NULL}$.
  - Xuất bảng kết quả chuẩn hóa `analysis_results.csv` và `features_quarterly.csv`.
- [x] **Phase 2.5: Lớp dự báo ĐV-ĐR — Controlled Nowcast/Forecast Engine (FCST-01…12)** — hoàn thành, quality gate fail-closed (xem §7)
  - Nowcast quý hiện tại ($h = 0$) trước khi có 10-Q và Forecast 1 quý tới ($h = 1$) cho các thành phần hoặc trực tiếp $E$.
  - Thuật toán: Baseline Naive/AR(1); mô hình chính Ridge Regression, Elastic Net hoặc Bayesian Ridge (nghiêm cấm Deep Learning vì cỡ mẫu $N \le 44$).
  - Khoảng tin cậy 80% & 95% (Conformal prediction / Bayesian interval), rào chắn Point-in-time guard (NFR-09).
  - Hệ thống cảnh báo tự động (Alert rules) và bóc tách top 3 yếu tố đóng góp (Driver Attribution qua SHAP/hệ số chuẩn hóa).
  - Kiểm định cuốn chiếu Rolling-origin backtest và Quality gate (FCST-08: bắt buộc beat Naive/AR(1) mới hiển thị nhãn forecast).
- [x] **Phase 3: Interactive Dashboard (Web UI)** — hoàn thành tại `web/` (7 view, không build step)
  - Xây dựng 7 chế độ xem hoàn chỉnh (DSH-01 đến DSH-07):
    - DSH-01: E Score theo quý
    - DSH-02: Input vs Output
    - DSH-03: Timeline sự kiện
    - DSH-04: Weight Sensitivity (0.6/0.4, 0.5/0.5, 0.7/0.3)
    - DSH-05: Trạng thái & bằng chứng (Data Status & Evidence)
    - DSH-06: Bối cảnh thị trường (Market Context)
    - DSH-07: Dự báo ĐV-ĐR — Forecast & Alerts (Nowcast/forecast $E$, interval 80%/95%, alert badge, top 3 driver attribution, link model card, nhãn experimental).
  - Triển khai hosting tĩnh trên GitHub Pages.

---

## 7. Phase 2 / 2.5 / 3 — trạng thái triển khai

### 7.1 Metric engine (Phase 2)

- Code: `src/aicor/compute/` — `metrics.py` (MA4Q, z16Q, `std=0`, Product Score), `features.py` (panel → feature matrix), `engine.py` (`In`, `Out`, `E` × 3 kịch bản), `provenance.py` (`source_id → source_url`).
- Cấu hình có phiên bản: `config/analysis.yaml` (`aicor-analysis-v1`).
- Artifact: `data/processed/features_quarterly.csv`, `data/processed/analysis_results.csv`, `data/processed/provenance.csv`, `data/processed/analysis_manifest.json` (SHA-256 từng file).
- `z16Q` = cửa sổ 16 quý gần nhất, tính riêng từng công ty. Với dữ liệu hiện tại: 7 quý/công ty có `E` (2024Q4→2026Q2); 15 quý đầu bị `insufficient_window` và **không** dùng cho `E`.
- Giá trị thiếu luôn là `NULL` + `reason`; không có 0 thay thế.

### 7.2 Lớp dự báo ĐV-ĐR (Phase 2.5)

- Code: `src/aicor/forecast/` — `snapshot.py` (point-in-time), `models.py` (naive / AR(1) / Ridge NumPy), `backtest.py` (rolling-origin + quality gate), `alerts.py`, `model_card.py`, `pulse.py`.
- Artifact: `forecast_results.csv`, `forecast_backtest.csv`, `forecast_coverage.csv`, `alert_log.csv`, `model_registry.json`, `model_card.md`.
- Horizon: `h=0` = quý hiện tại chưa có 10-Q; `h=1` = quý kế tiếp. Target = `E` trực tiếp (ghi trong config).
- **Kết quả thực tế trên dữ liệu hiện tại:** quality gate **không đạt** (Ridge 1.05 MAE so với naive 0.66 ở h=0; 1.04 so với 1.03 ở h=1). Vì vậy toàn bộ kết quả Pulse hiển thị là `insufficient_evidence`, alert bị `suppressed`. Đây là hành vi đúng theo FCST-08, không phải lỗi.

### 7.3 Dashboard (Phase 3)

- Một frontend duy nhất tại `web/`: `index.html` + `assets/{app.js,chart.js,styles.css}`, không framework runtime, không build step.
- 7 view DSH-01…07; dữ liệu chỉ đọc từ `web/data/manifest.json` → `runs/<run_id>.json` (payload bất biến, kiểm tra SHA-256 trước khi render).
- Có loading / empty / stale / partial / error state; tab có điều hướng bàn phím; biểu đồ có điểm dữ liệu focusable + tooltip; bảng số liệu trong `<details>`; tôn trọng `prefers-reduced-motion`; responsive; light/dark theo hệ điều hành.
- Trình duyệt **không** tính lại chỉ số nghiên cứu và **không** gọi crawler.

### 7.4 Vận hành

```bash
uv run python -m aicor.pipeline.run --stage collect   # 4 nguồn, retry/backoff, cô lập lỗi
uv run python -m aicor.pipeline.run --stage preprocess
uv run python -m aicor.pipeline.run --stage analysis   # compute + Pulse + publish
uv run python -m aicor.pipeline.run --stage all
python -m http.server 8765 --directory web             # xem dashboard local
```

- Publish atomic: payload ghi vào `runs/<run_id>.json` (fsync) rồi mới thay `manifest.json`.
- Dashboard poll manifest mỗi 30 giây và kiểm tra checksum trước khi render.
- Lịch: `.github/workflows/pipeline.yml` (4 lần/ngày, `concurrency` chống chạy trùng); lock trong `data/.pipeline.lock` có thu hồi lock cũ.
- **Không có SLA/24×7:** chưa có uptime monitoring; GitHub Actions cron có thể bị trễ.
