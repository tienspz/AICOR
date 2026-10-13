# AICOR — AI Investment & Corporate Outcome Research

[![Validate](https://github.com/tienspz/AICOR/actions/workflows/validate.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/validate.yml)
[![Crawl SEC](https://github.com/tienspz/AICOR/actions/workflows/crawl-sec.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/crawl-sec.yml)
[![Crawl Market](https://github.com/tienspz/AICOR/actions/workflows/crawl-market.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/crawl-market.yml)
[![Crawl Trends](https://github.com/tienspz/AICOR/actions/workflows/crawl-trends.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/crawl-trends.yml)
[![Crawl IR](https://github.com/tienspz/AICOR/actions/workflows/crawl-ir.yml/badge.svg)](https://github.com/tienspz/AICOR/actions/workflows/crawl-ir.yml)

Hệ thống thu thập dữ liệu định lượng, tiền xử lý và so sánh mức đầu vào liên quan đến AI ($In$) với các chỉ báo đầu ra AI ($Out$) theo quý giữa **Microsoft Corporation (MSFT)** và **Alphabet Inc. (GOOGL)**.

Kết quả đo lường là điểm tương đối:

$$E = Out - In$$

> **Lưu ý liêm chính nghiên cứu:** Điểm $E$ là thước đo tương đối để quan sát xu hướng lịch sử và kiểm tra độ nhạy trọng số; không phải ROI, lợi nhuận hay bằng chứng quan hệ nhân quả (SRS §1.1).

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
│               AUTOMATION & VERIFICATION (GitHub Actions)               │
│  - 4 Cron Crawlers định kỳ tự động lưu data & manifests về repo         │
│  - Validate gate chạy tự động trên push/PR (65/65 tests green)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Nguồn dữ liệu & Lịch thu thập tự động (Rate Limit & Schedules)

Các crawler hoạt động độc lập (NFR-04: một nguồn lỗi không làm ảnh hưởng nguồn khác), lưu bản snapshot nguyên gốc kèm mã hash SHA-256 trong `manifest.csv` và ghi nhật ký 16 trường vào `data/sync_log.jsonl`.

| Nguồn | Tier | URL Canonical | Chu kỳ tự động (GitHub Actions) | Rate Limit / Cơ chế an toàn |
| :--- | :---: | :--- | :--- | :--- |
| **SEC EDGAR XBRL** | **Tier S** | `data.sec.gov/api/xbrl/companyfacts/` | `0 */6 * * *` (Mỗi 6 tiếng) | `REQUEST_DELAY = 0.1s` (≤ 10 req/s, NFR-07); khai báo User-Agent; Tag resolver linh hoạt theo kỳ |
| **Market Data** | **Tier B** | Yahoo Finance (`yfinance`) | `0 13-20 * * 1-5` (Sau phiên giao dịch) | Giữ nguyên `adj_close` và `volume`, lưu CSV định kỳ (SRC-09) |
| **Google Trends** | **Tier B** | Google Trends (`pytrends`) | `0 */12 * * *` (Mỗi 12 tiếng) | Circuit-breaker tự động fallback `TrendsUnavailable` (§7.4) |
| **IR & Product Blogs** | **Tier A** | Microsoft & Google Official Blogs | `0 2 * * *` (Hằng ngày lúc 02:00 UTC) | Chuẩn hóa URL, dedup bài viết đa kênh, phân loại A/B/C theo rubric |

---

## 3. Cấu trúc thư mục

```text
├── .github/workflows/          # 5 GitHub Actions workflows (CI + 4 Cron Crawlers)
│   ├── validate.yml            # Chạy test suite & data quality gates trên push/PR
│   ├── crawl-sec.yml           # Cron crawl SEC XBRL (Tier S) + auto-preprocess
│   ├── crawl-market.yml        # Cron crawl Yahoo Finance (Tier B) + auto-preprocess
│   ├── crawl-trends.yml        # Cron crawl Google Trends (Tier B) + auto-preprocess
│   └── crawl-ir.yml            # Cron crawl IR Blogs (Tier A) + auto-preprocess
├── data/                       # Dữ liệu thu thập và manifest truy vết
│   ├── raw/                    # Snapshots dữ liệu thô bất biến (sec, market, trends, ir)
│   ├── processed/              # 5 tập dữ liệu tiền xử lý chuẩn hóa dạng bảng (Lecture 07)
│   │   ├── financial_quarterly.csv     # Bảng tài chính 22 quý, chuẩn hóa triệu USD, Q4=FY-9M
│   │   ├── panel_quarterly.csv         # Bảng panel hợp nhất (is_msft, rd_intensity, capex_intensity)
│   │   ├── ai_products.csv             # 40 sự kiện AI đã gán nhãn A/B/C kèm giải trình
│   │   ├── google_trends_quarterly.csv # Điểm xu hướng tìm kiếm gộp trung bình theo quý
│   │   └── market_quarterly.csv        # Giá đóng cửa điều chỉnh TB & tổng volume theo quý
│   └── sync_log.jsonl          # Nhật ký đồng bộ 16 trường (SRS §6.7)
├── docs/                       # Tài liệu kiến trúc và kế hoạch
│   ├── decisions/              # Baseline params & config (baseline.yaml, trends_config.yaml)
│   ├── setup/                  # Hướng dẫn thiết lập môi trường
│   ├── planning/               # Kế hoạch chi tiết và ma trận truy vết
│   └── superpowers/plans/      # Kế hoạch triển khai kỹ thuật
├── rubric/v1.yaml              # Rubric phân loại sản phẩm A/B/C (provisional)
├── src/aicor/                  # Mã nguồn chính của AICOR
│   ├── config.py               # Settings, CIK MSFT/GOOGL, rate limits
│   ├── sources/                # 4 crawlers độc lập & registry contract
│   │   ├── sec.py              # SEC XBRL crawler & period-aware tag resolver
│   │   ├── market.py           # yfinance market data fetcher
│   │   ├── trends.py           # Google Trends fetcher + circuit breaker
│   │   ├── ir.py               # IR blog scraper & A/B/C classifier
│   │   └── registry.py         # Data contracts (SourceRecord, SyncRecord)
│   ├── preprocess/             # Tiền xử lý dữ liệu (Lecture 07)
│   │   ├── extract.py          # Trích xuất XBRL JSON facts sang DataFrame & Q4 derivation
│   │   ├── cleaning.py         # Thao tác 1: Làm sạch dữ liệu
│   │   ├── missing.py          # Thao tác 2: Chính sách xử lý dữ liệu thiếu (NULL)
│   │   ├── transform.py        # Thao tác 3: Chuyển đổi YTD→Quý & chuẩn hóa lịch
│   │   ├── integrate.py        # Thao tác 4: Tích hợp dữ liệu & tạo biến giả (dummies)
│   │   ├── scale.py            # Thao tác 5: Chuẩn hóa tỉ lệ (z-score, MA4Q)
│   │   └── features.py         # Metadata truy vết biến phái sinh
│   └── pipeline/               # Điều phối pipeline 8 bước (SRS §9)
│       ├── archive.py          # Ghi manifest SHA-256 và sync_log
│       └── run.py              # run_pipeline & run_full_pipeline CLI
├── tests/                      # Bộ kiểm thử tự động (65 tests)
│   ├── contract/               # Kiểm thử schema & bất biến dữ liệu
│   ├── unit/                   # Kiểm thử logic tiền xử lý và rubric
│   └── integration/            # Kiểm thử tích hợp crawler & pipeline E2E
├── pyproject.toml              # Cấu hình dự án Python & dependencies
└── SPEC.md                     # Đặc tả yêu cầu hệ thống SRS Baseline
```

---

## 4. Cài đặt & Sử dụng

### 4.1 Yêu cầu môi trường
- Python `>= 3.12`
- Trình quản lý gói [`uv`](https://github.com/astral-sh/uv) (khuyến nghị) hoặc `pip`

### 4.2 Cài đặt dependencies
```bash
git clone https://github.com/tienspz/AICOR.git
cd AICOR

# Đồng bộ môi trường bằng uv
uv sync --all-extras
```

### 4.3 Chạy bộ kiểm thử (Unit, Contract, E2E)
```bash
# Chạy toàn bộ offline test suite
uv run pytest -v

# Chạy kèm báo cáo độ phủ mã nguồn (coverage)
uv run pytest --cov=src/aicor tests/
```

### 4.4 Chạy crawler độc lập thủ công
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

### 4.5 Chạy Pipeline tiền xử lý dữ liệu (End-to-End)
```bash
# Đọc toàn bộ data/raw/, thực thi 9 phép chuẩn hóa (Lecture 07) và xuất 5 file CSV vào data/processed/
uv run python -m aicor.pipeline.run
```
> **Tự động hóa hoàn toàn trên GitHub Actions:** Mỗi khi bất kỳ crawler cron nào chạy thành công, GitHub Actions sẽ tự động thực thi bước này, xác thực qua kiểm thử dữ liệu và commit cả `data/raw/` lẫn `data/processed/` ngược về repository!

---

## 5. Nguyên tắc thiết kế cốt lõi (NFRs)

- **NFR-01 (Tính tái lập):** Mọi file snapshot đều lưu kèm mã băm SHA-256 trong `manifest.csv`. Cùng đầu vào + cùng tham số công thức cho ra kết quả đồng nhất.
- **NFR-02 (Tính truy vết):** Mọi dòng dữ liệu phân tích đều có `source_id` dẫn về tài liệu gốc của công ty.
- **NFR-03 (Quản lý phiên bản cấu hình):** Tham số rolling window, rubric trọng số nằm trong `docs/decisions/baseline.yaml` và `rubric/v1.yaml`.
- **NFR-04 (Khả năng chịu lỗi):** Lỗi ở 1 nguồn (ví dụ Google Trends chặn IP) sẽ chuyển trạng thái sang `partial`, bảo toàn toàn bộ dữ liệu SEC/IR mà không bị rollback.
- **NFR-06 (Bảo mật):** Không hardcode API key/secret. User-Agent lấy từ biến môi trường `SEC_USER_AGENT`.
- **NFR-07 (Tuân thủ nguồn):** Tuân thủ giới hạn SEC `≤ 10 req/s` bằng bộ điều phối thời gian cố định.

---

## 6. Lộ trình phát triển tiếp theo

- [x] **Phase 1: Data Collection & Preprocessing** (Hoàn thành — 65/65 tests green, 5 GitHub Actions workflows live).
  - Tầng raw bất biến (SEC facts XBRL, Market 1,255 bars, Trends 1,004 rows, IR 40 products).
  - Tầng processed chuẩn hóa: 5 bảng CSV tại `data/processed/` (44 quý từ 2021-Q1 đến 2026-Q2).
  - Khắc phục triệt để logic cross-tag Q4 cho GOOGL: $Q_4 = FY - 9M$, cân đối $|Assets - (Liabilities + Equity)| = 0.0$.
  - Tự động hóa khép kín: Tự động crawl, tiền xử lý, kiểm tra chất lượng và commit/push trên GitHub Actions.
- [ ] **Phase 2: Metric Computation Engine ($In$, $Out$, $E$)**
  - Tính toán $In = z(\text{R\&D})$ đối xứng cho 2 công ty.
  - Tính toán $Out = w_1 \cdot z(\text{Product MA4Q}) + w_2 \cdot z(\text{Trends MA4Q})$ với 3 kịch bản trọng số độ nhạy ($0.6/0.4, 0.5/0.5, 0.7/0.3$).
  - Xử lý các case ngoại lệ: $std = 0 \to \text{degenerate}$, $< 4$ quý $\to \text{NULL}$.
  - Xuất bảng kết quả chuẩn hóa `analysis_results.csv` và `features_quarterly.csv`.
- [ ] **Phase 3: Interactive Dashboard (Web UI)**
  - Xây dựng 6 chế độ xem (DSH-01 Điểm E, DSH-02 Input/Output, DSH-03 Timeline sự kiện, DSH-04 Độ nhạy trọng số, DSH-05 Trạng thái & bằng chứng, DSH-06 Bối cảnh thị trường).
  - Triển khai hosting tĩnh trên GitHub Pages.
