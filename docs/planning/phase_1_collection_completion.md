# AICOR — Phase 1: Data Collection & Preprocessing Completion Report

**Date:** 2026-10-13  
**Status:** COMPLETE & VERIFIED  
**Target:** Microsoft Corporation (MSFT, CIK 789019) & Alphabet Inc. (GOOGL, CIK 1652044)  

---

## 1. Mục tiêu & Kết quả thực tế

Giai đoạn Phase 1 đã hoàn thành toàn bộ mục tiêu theo Lecture 07 và SRS Baseline ([SPEC.md](../../SPEC.md)):

1. **4 Bộ thu thập dữ liệu độc lập (Crawlers):**
   - **SEC EDGAR (Tier S):** Thu thập toàn bộ fact tài chính XBRL định kỳ. Tích hợp bộ giải quyết thẻ (tag resolver) linh hoạt theo từng kỳ, xử lý thay đổi thẻ XBRL của GOOGL (`Revenues` vs `Revenue`), fail-loud khi thiếu thẻ (`TagResolutionError`).
   - **Market Data (Tier B):** Thu thập giá giao dịch lịch sử 5 năm qua `yfinance` cho MSFT và GOOGL.
   - **Google Trends (Tier B):** Thu thập chuỗi mức độ quan tâm tìm kiếm lịch sử cho 4 từ khóa chủ chốt. Tích hợp circuit-breaker (`TrendsUnavailable`) khi bị giới hạn IP để kích hoạt fallback trọng số ở Phase 2.
   - **IR & Product Blogs (Tier A):** Cào dữ liệu bài viết từ 4 blog chính thức của Microsoft và Google. Chuẩn hóa URL loại bỏ trùng lặp và tự động phân loại A/B/C theo [rubric/v1.yaml](../../rubric/v1.yaml).

2. **Cơ chế kiểm soát truy cập & Rate Limiting (NFR-07):**
   - **Định lượng SEC:** Giới hạn tối đa 10 requests/giây (`REQUESTS_PER_SEC = 10`, `REQUEST_DELAY = 0.1s`).
   - **User-Agent định danh:** Tuân thủ yêu cầu bắt buộc của SEC EDGAR, lấy từ biến môi trường `SEC_USER_AGENT` hoặc fallback `"AICOR-research/1.0 (contact: repo README)"`.
   - **Lịch trình tự động hoá GitHub Actions (PIPE-01):**
     - SEC EDGAR: `0 */6 * * *` (mỗi 6 tiếng).
     - Market: `0 13-20 * * 1-5` (sau giờ đóng cửa thị trường các ngày trong tuần).
     - Trends: `0 */12 * * *` (mỗi 12 tiếng).
     - IR Blogs: `0 2 * * *` (mỗi ngày lúc 02:00 UTC).
     - CI Validation: Tự động chạy mỗi lần push và PR trên các nhánh chính.

3. **Tính toàn vẹn dữ liệu & Khả năng chịu lỗi (NFR-01, NFR-02, NFR-04):**
   - **Append-only & SHA-256:** Mọi dữ liệu crawl được lưu dạng snapshot bất biến; cập nhật mã băm SHA-256 vào `manifest.csv`.
   - **16-field Sync Log:** Ghi chi tiết từng lần chạy vào `data/sync_log.jsonl`.
   - **Chịu lỗi từng phần:** Lỗi đơn nguồn (ví dụ Trends bị chặn) chuyển trạng thái pipeline sang `partial`, bảo toàn toàn bộ dữ liệu tài chính của SEC.

4. **Quy trình tiền xử lý & Xuất dữ liệu bảng chuẩn hóa (Lecture 07 — 9 Operations):**
   - [x] Làm sạch (Cleaning): Strip khoảng trắng, ép kiểu số, lọc dòng rác.
   - [x] Dữ liệu thiếu (Missing): Áp dụng chính sách `NULL` + lý do rõ ràng, tuyệt đối không tự điền 0.
   - [x] Chuyển đổi (Transform): Công thức $Q_4 = FY - 9M$, căn chỉnh quý lịch DAT-01 theo `period_end_date`, quy đổi đơn vị về triệu USD.
   - [x] Tích hợp (Integrate): Ghép bảng panel, tạo biến giả công ty `is_msft` ($k-1$), tính Product Score sơ bộ ($3A+2B+1C$), one-hot sự kiện.
   - [x] Chuẩn hóa thang đo (Scale): Rolling z-score 16 quý với guard xử lý $\sigma=0$ (`degenerate`), trung bình động MA4Q nghiêm ngặt đủ 4 quý, phát hiện outlier dựa trên IQR QoQ.
   - [x] **Trích xuất & Tái tạo tự động (`aicor.preprocess.extract` & `aicor.pipeline.run`):**
     - Đã tạo 5 bảng CSV sạch tại `data/processed/`:
       1. `financial_quarterly.csv`: 44 hàng (22 quý × 2 công ty) chuẩn hóa đơn vị triệu USD.
       2. `panel_quarterly.csv`: Bảng panel hợp nhất với `is_msft`, `rd_intensity`, `capex_intensity`.
       3. `ai_products.csv`: 40 sự kiện AI đã phân loại A/B/C kèm lý do giải trình.
       4. `google_trends_quarterly.csv`: Điểm quan tâm tìm kiếm gộp trung bình theo quý.
       5. `market_quarterly.csv`: Giá đóng cửa điều chỉnh TB và tổng khối lượng giao dịch quý.
     - **Giải quyết triệt để Q4 GOOGL:** Sửa đổi logic gom nhóm liên tag (cross-tag pooling) để tính đúng $Q_4 = FY - 9M$ thay vì lấy nhầm số cả năm $FY$.
     - **Cân đối kế toán tuyệt đối:** Phương trình kế toán $|Assets - (Liabilities + Equity)| = 0.0$ trên 100% 44 quý.
     - **Tích hợp CI:** Cả 4 workflow GitHub Actions tự động thực thi tiền xử lý và commit `data/processed/` cùng `data/raw/` lên GitHub.

---

## 2. Bảng đối chiếu nghiệm thu (Acceptance Matrix)

| Mã yêu cầu | Mô tả | Trạng thái | Minh chứng |
| :--- | :--- | :---: | :--- |
| **SRC-01** | Mô hình 4 Tier nguồn (S, A, B, R) | Đạt | `SourceRecord` chỉ chấp nhận S/A/B; cấm Tier R |
| **SRC-03** | Mọi quan sát có `source_id` | Đạt | `run_pipeline` gán và xác thực `source_id` không null |
| **SRC-04** | Dữ liệu SEC là chuẩn khi xung đột | Đạt | `sec.py` lấy dữ liệu gốc từ SEC EDGAR API |
| **SRC-05** | Dữ liệu thiếu ghi rõ `reason` | Đạt | `missing.py` điền `status="unavailable"` và `reason` |
| **SRC-09** | Không crawl lại khi đã có snapshot | Đạt | Cơ chế manifest + SHA-256 đối chiếu snapshot |
| **DAT-01** | Căn chỉnh quý lịch theo `period_end_date` | Đạt | `align_calendar` chuyển `period_end_date` sang calendar quarter |
| **PIPE-01** | Lịch trình tự động hoá đa nguồn | Đạt | 4 GitHub Actions cron workflows hoạt động độc lập + auto-preprocess |
| **NFR-01** | Khả năng tái lập kết quả | Đạt | SHA-256 manifest + mã nguồn kiểm thử xác định |
| **NFR-04** | Lỗi 1 nguồn không xóa dữ liệu nguồn khác | Đạt | Test `test_e2e_partial_on_source_failure` pass |
| **NFR-07** | Tuân thủ rate limit và User-Agent | Đạt | Rate limit $\le 10$ req/s và User-Agent tuân thủ SEC |

---

## 3. Trạng thái kiểm thử & Tự động hóa CI (CI/CD Status)

- **Tổng số tests:** 65 tests (bao gồm 7 contract tests, 19 integration tests, 39 unit tests).
- **Kết quả:** 65/65 PASSED (100%).
- **Độ phủ mã nguồn (Coverage):** 65% trên toàn bộ các module core.
- **GitHub Actions Workflows:** 5/5 workflows hoạt động thành công (Success):
  - `validate.yml`: Chạy tự động trên Push/PR.
  - `crawl-sec.yml`, `crawl-market.yml`, `crawl-trends.yml`, `crawl-ir.yml`: Tự động crawl định kỳ + tự động chạy `aicor.pipeline.run` để cập nhật `data/processed/` + commit & push về nhánh `main`.

---

## 4. Chuyển giao sang Phase 2

Cơ sở dữ liệu thô và toàn bộ bảng dữ liệu tiền xử lý chuẩn hóa đã hoàn tất và sẵn sàng. Giai đoạn tiếp theo (Phase 2) sẽ tập trung vào:
1. Xây dựng module tính toán cốt lõi: `src/aicor/compute/engine.py`.
2. Tính $In = z(\text{RD})$ (R&D Expense) và $Out = w_1 \cdot z(\text{Product MA4Q}) + w_2 \cdot z(\text{Trends MA4Q})$.
3. Tính $E = Out - In$ trên 3 kịch bản độ nhạy trọng số (Base 0.6/0.4, Equal 0.5/0.5, Tech 0.7/0.3).
4. Xuất các bảng phân tích sẵn sàng cho Dashboard: `analysis_results.csv` và `features_quarterly.csv`.
