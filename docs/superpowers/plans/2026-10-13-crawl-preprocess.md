# Crawl + Tiền xử lý (Lecture 07) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crawl dữ liệu thật từ 5 nguồn canonical (SEC, Yahoo, Trends, IR) về repo, tiền xử lý theo đúng 9 operations của Lecture 07, push lên `https://github.com/tienspz/AICOR`, tự động hóa bằng GitHub Actions.

**Architecture:** `src/aicor/sources/` (4 crawler độc lập, Collect+Archive) → `src/aicor/preprocess/` (Cleaning → Missing → Transform → Integrate → Scale, đúng thứ tự slide p16) → `src/aicor/pipeline/` (Validate gates + sync_log). Mỗi crawler ghi raw append-only + SHA-256, không crawler nào được ghi đè dữ liệu của crawler khác (NFR-04). Dashboard KHÔNG nằm trong phase này.

**Tech Stack:** Python 3.14, `uv`, pandas, NumPy, pytest, `yfinance`, `pytrends`, GitHub Actions (cron), CSV append-only + SQLite/JSON (§12).

**Spec:** `SPEC.md` (AICOR-SRS Baseline, 636 dòng) + `Lecture 07 - Data Preprocessing.pdf` (17 slides).

## Global Constraints

- Phạm vi công ty KHÓA: Microsoft (MSFT, CIK `789019`, fiscal year end June 30) và Alphabet (GOOGL/GOOG, CIK `1652044`, fiscal year end December 31) — SPEC mục 0 Quyết định 1.
- Canonical URLs (SPEC §3.3): `https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json`, `https://data.sec.gov/api/xbrl/companyfacts/CIK0001652044.json`, `https://www.sec.gov/edgar/browse/?CIK=789019`, `https://www.sec.gov/edgar/browse/?CIK=1652044`, Yahoo `MSFT`/`GOOGL`, blogs MSFT/Azure/Google/Cloud, Google Trends.
- SEC client PHẢI khai báo User-Agent phù hợp; tôn trọng `robots.txt` + rate limit (NFR-07). Nasdaq bị LOẠI khỏi nguồn (SPEC §3.3).
- `value = NULL`, `status = unavailable`, `reason` ghi rõ lý do cho dữ liệu thiếu; KHÔNG điền 0, KHÔNG bịa giá trị (SRC-05, SRC-07).
- `In = z(R&D theo quý)` đối xứng cho cả 2 công ty (Quyết định 2). `Out = 0.6*z(Product MA4Q) + 0.4*z(Trends MA4Q)`; sensitivity `0.5/0.5`, `0.7/0.3` (§7.4).
- MA4Q yêu cầu đủ 4 quý, không MA ngắn hơn (§7.2). `z = (x-mean)/std`; `std=0` → ghi trạng thái, không chia 0 (§7.3, §7.5). Không tính `E` khi `In`/`Out` thiếu (§7.5).
- `period_end_date` là khóa so sánh chéo (DAT-01); `fiscal_period` chỉ hiển thị. Q4 = FY − 9M, KHÔNG lấy fact 3M cho Q4 (§6.2).
- Dashboard không crawl trực tiếp nguồn ngoài (PIPE-02). Lịch crawl là đề xuất, không phải SLA (PIPE-01): market nhịp nhanh sau phiên; SEC/IR/events nhịp chậm hằng ngày.
- Token/API key trong secrets/environment, không commit (NFR-06). Raw binaries (`*.htm`, `data/raw/sec_documents/`, `data/raw/ir_documents/`) KHÔNG commit — chỉ commit manifest SHA-256 + URL (xem `.gitignore` hiện tại).
- Mọi derived feature phải có method + source + confidence (§6.1). Mọi điểm dữ liệu phân tích phải có `source_id` (SRC-03). SEC là chuẩn khi xung đột (SRC-04 → dùng SEC).
- Testing (§12): unit test cho normalize, gộp quý, Product Score, MA4Q, z-score, In/Out/E, missing-data.

## Field–Feature → Mục tiêu (bắt buộc: mọi field ánh xạ tới RQ/DSH)

| Field / Feature (SPEC §6–§8.3) | Lecture 07 operation | Phục vụ RQ | Hiện ở DSH |
| --- | --- | --- | --- |
| `revenue`, `rd_expense`, `filing_date`, `period_end_date` (§6.2, Tier S) | Raw → Cleaning → Transform (YTD→Q) → z-score → `In` | RQ-01 | DSH-02 |
| `capex`, `capex_intensity = CapEx/Revenue` (§6.2, §7.4 Could) | Derived variable (kiểu Price/Area, slide 3/9) | RQ-01 (đối chiếu) | DSH-02 |
| `product_name`, `announcement_date`, `category_abc`, `category_rationale` (§6.3, Tier A) → `product_score = 3A+2B+1C` → MA4Q | Derived + Reshaping (gộp quý) | RQ-02 | DSH-02 |
| `keyword`, `geo`, `timeframe`, `interest_score` (§6.4, Tier B) → Trends quarterly → min-max 16Q → MA4Q | Scaling/Normalization + Reshaping | RQ-02 | DSH-02 |
| `In`, `Out`, `E` (§7.4, §8.3) | Scaling (z-score, non-tree-like → bắt buộc, slide 5/5) | RQ-03 | DSH-01 |
| 3 bộ trọng số (§7.4) | Sensitivity (lưu `config_version`) | RQ-04 | DSH-04 (phase sau) |
| `event_type`, `event_name`, `amount` (§6.5) | Categorical → dummy/one-hot (KHÔNG label-encoding vì Out là linear, slide 8/9) | Bối cảnh RQ-02/03 | DSH-03 (phase sau) |
| `ticker`, `adj_close`, `volume` (§6.6, Tier B) | Raw → Cleaning, KHÔNG đưa vào `E` | Bối cảnh | DSH-06 (phase sau) |
| `company_id` (MSFT/GOOGL) | Dummy `is_msft` (k−1=1 dummy, slide 5/9) cho join/đối chiếu | Tất cả RQ | Mọi DSH |
| `year`, `calendar_quarter` từ `period_end_date`/`announcement_date` | Derived Date→Year/Quarter (slide 1/9) | Join DAT-01 | Mọi DSH |
| `sync_log`, `data_quality_log`, `source_registry` (§6.7, §8.1) | Monitor (§9 bước 8) | Trust (NFR-02) | DSH-05 (phase sau) |

## Review Focus

- Q4 của cả 2 công ty không có 10-Q riêng: implementer có thể vô tình lấy fact 3M gán cho Q4 — mong đợi Q4 luôn = FY − 9M và test pin việc này (Task 9).
- GOOGL đổi tag XBRL giữa kỳ (`Revenues` vs tag cũ sau 2025-03-31): resolver chọn tag theo từng period, thiếu tag → fail loud chứ không silent NULL (Task 4).
- Hai lần query Trends độc lập có thang 0–100 không so sánh được: mong đợi freeze 1 query lịch sử duy nhất + ghi `timeframe` vào registry, không nối thang (Task 6).
- MSFT fiscal (kết thúc 30/6) lệch calendar quarter: mong đợi join chéo luôn dùng `period_end_date`, `fiscal_period` chỉ hiển thị (Task 9).
- Filing trễ một công ty: mong đợi pipeline giữ dữ liệu cũ nguyên vẹn, ghi `partial`, không xóa/quay lui (NFR-04) — test giả lập 1 nguồn fail (Task 12).

---

### Task 1: Nối remote + baseline commit + push GitHub

**Files:**
- Modify: `.gitignore` (chỉ nếu thiếu rule — hiện đã đủ, không sửa nếu không cần)
- Verify: `SPEC.md` (` M` hiện tại) được commit

**Interfaces:**
- Consumes: repo local hiện tại (5 commits, branch hiện tại)
- Produces: remote `origin = https://github.com/tienspz/AICOR`, branch chính đã push

- [ ] **Step 1: Kiểm tra trạng thái sạch để commit**

Run: `git status --short; git log --oneline -3`
Expected: chỉ thấy ` M SPEC.md`, không có file secret/`.env` nào untracked

- [ ] **Step 2: Commit SPEC.md baseline**

Run: `git add SPEC.md && git commit -m "docs(SPEC): adopt rewritten SRS baseline (E = Out - In)"`
Expected: `git status --short` trống

- [ ] **Step 3: Gắn remote và push (không dùng `gh` vì chưa cài)**

Run: `git remote add origin https://github.com/tienspz/AICOR.git; git branch -M main; git push -u origin main`
Expected: push thành công; `git ls-remote origin` liệt kê `main`. Nếu GitHub hỏi auth: tạo PAT (classic, scope `repo`) trên github.com → dùng làm password; KHÔNG paste PAT vào chat/file

- [ ] **Step 4: Xác minh trên web**

Mở `https://github.com/tienspz/AICOR` kiểm tra `SPEC.md` hiển thị ở root
Expected: thấy file, commit message đúng

---

### Task 2: Scaffold Python (`uv`, config, secrets)

**Files:**
- Create: `pyproject.toml`, `.env.example`, `src/aicor/__init__.py`, `src/aicor/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: SPEC §3.3 (URLs), §12 (Python/pandas/NumPy), NFR-06/07
- Produces: `get_settings() -> Settings` với `sec_user_agent: str`, `companies: dict`; `COMPANY_CIK = {"MSFT": "789019", "GOOGL": "1652044"}`; `REQUESTS_PER_SEC <= 10`

- [ ] **Step 1: Write the failing test**

```python
def test_settings_require_user_agent():
    s = get_settings(env={})
    assert "AICOR" in s.sec_user_agent  # SPEC §5: SEC yêu cầu UA phù hợp
    assert COMPANY_CIK == {"MSFT": "789019", "GOOGL": "1652044"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL (`get_settings` chưa tồn tại)

- [ ] **Step 3: Implement `get_settings` + `COMPANY_CIK` trong `src/aicor/config.py`**

Đọc `SEC_USER_AGENT` từ env, default `"AICOR-research/1.0 (contact: repo README)"`; hằng số CIK verbatim từ SPEC

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example src/aicor tests/test_config.py
git commit -m "feat: scaffold python project with SEC user-agent config"
git push
```

---

### Task 3: Contract `source_registry` + `sync_log` (contract-first)

**Files:**
- Create: `src/aicor/sources/registry.py`, `src/aicor/pipeline/archive.py` (chỉ phần ghi manifest/log, chưa crawl)
- Test: `tests/contract/test_registry_schema.py`

**Interfaces:**
- Consumes: SPEC SRC-01/03 (§8.1 bảng 2, 11), §6.7 field list, `get_settings` (Task 2)
- Produces: `SourceRecord` dataclass (fields: `source_id, company, metric, source_type, source_tier, source_url, reporting_period, filing_date, access_date, primary_or_secondary, verification_status, xbrl_tag, period_basis`); `write_sync_log(...) -> SyncRecord`; `sha256_file(path) -> str`

- [ ] **Step 1: Write the failing test**

```python
def test_registry_rejects_tier_r():
    with pytest.raises(ValueError):
        SourceRecord(source_id="X", source_tier="R", ...)  # Tier R không vào registry (SRC-01)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/contract/test_registry_schema.py -v`
Expected: FAIL (class chưa tồn tại)

- [ ] **Step 3: Implement `SourceRecord` (frozen dataclass, validator `source_tier in {"S","A","B"}`) và `write_sync_log` với đủ 16 field §6.7 (`run_id … missing_reason`)**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/contract/test_registry_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicor/sources/registry.py src/aicor/pipeline/archive.py tests/contract/test_registry_schema.py
git commit -m "feat: add source_registry and sync_log contracts"
git push
```

---

### Task 4: SEC crawler — financial/R&D (RQ-01, Tier S)

**Files:**
- Create: `src/aicor/sources/sec.py`, `data/raw/sec/` (snapshots JSON, tracked), manifest `data/raw/sec/manifest.csv`
- Test: `tests/integration/test_sec_crawler.py` (dùng fixture ghi sẵn; chỉ test live khi `-m live`)

**Interfaces:**
- Consumes: `get_settings`, `SourceRecord`, `write_sync_log`, `sha256_file` (Tasks 2–3)
- Produces: `fetch_companyfacts(cik: str) -> dict` (raw JSON); `resolve_metric(facts: dict, tag_candidates: list[str], period_end: date) -> tuple[value|None, xbrl_tag|None]` (period-aware, fail loud khi thiếu tag — ADR-0004); raw snapshot `sec_{CIK}_{retrieved_at}.json` + SHA-256

- [ ] **Step 1: Write the failing test (dùng fixture, không chạm mạng)**

```python
def test_resolve_googl_revenue_tag_switch(fixture_googl_facts):
    v1, tag1 = resolve_metric(fixture_googl_facts, ["Revenues", "Revenue"], date(2024, 12, 31))
    v2, tag2 = resolve_metric(fixture_googl_facts, ["Revenues", "Revenue"], date(2026, 3, 31))
    assert (tag1, tag2) == ("Revenue", "Revenues")  # tag chết ở 2025-03-31
    with pytest.raises(TagResolutionError):
        resolve_metric({}, ["Revenues"], date(2026, 3, 31))  # fail loud, không silent NULL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_sec_crawler.py -v -m "not live"`
Expected: FAIL (`resolve_metric` chưa tồn tại)

- [ ] **Step 3: Implement `fetch_companyfacts` (header UA từ settings, ≤10 req/s, lưu snapshot + SHA-256) và `resolve_metric` (duyệt `tag_candidates` theo từng period, hết tag → `TagResolutionError`)**

Chỉ crawl metrics §6.2: `revenue, rd_expense, capex, operating_income, net_income, cfo, assets, liabilities, equity, shares, eps` + `filing_date` từ submissions API

- [ ] **Step 4: Run tests (offline) + 1 lần live kiểm chứng**

Run: `uv run pytest tests/integration/test_sec_crawler.py -v -m "not live"`
Expected: PASS. Sau đó live 1 lần: `uv run pytest tests/integration/test_sec_crawler.py -v -m live` (kiểm tra 21 quý revenue mỗi công ty — FR_T01 sơ bộ)

- [ ] **Step 5: Commit (chỉ manifest + CSV, KHÔNG commit `*.htm` — đã ignore)**

```bash
git add src/aicor/sources/sec.py tests/integration/test_sec_crawler.py data/raw/sec/manifest.csv
git commit -m "feat: add SEC XBRL crawler with period-aware tag resolver"
git push
```

---

### Task 5: Market crawler — `yfinance` (bối cảnh DSH-06, Tier B)

**Files:**
- Create: `src/aicor/sources/market.py`
- Test: `tests/integration/test_market_crawler.py`

**Interfaces:**
- Consumes: `SourceRecord`, `write_sync_log` (Task 3)
- Produces: `fetch_market(ticker: str, period: str = "5y") -> pandas.DataFrame` với cột `date, open, high, low, close, adj_close, volume` (SRC-01 Tier B bắt buộc); `save_market_csv(df, ticker) -> path` vào `data/raw/market/`

- [ ] **Step 1: Write the failing test**

```python
def test_market_columns_match_src01():
    df = fetch_market("MSFT", period="1mo", offline_fixture=True)
    assert list(df.columns) == ["date", "open", "high", "low", "close", "adj_close", "volume"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_market_crawler.py -v -m "not live"`
Expected: FAIL

- [ ] **Step 3: Implement `fetch_market` qua `yfinance` (auto_adjust=False để giữ `adj_close` riêng; 1 lần tải rồi lưu CSV — SRC-09, không tải lại mỗi lần chạy)**

Tickers: `MSFT`, `GOOGL` (SPEC §3.3). Ghi `access_date` + ticker vào registry

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_market_crawler.py -v -m "not live"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicor/sources/market.py tests/integration/test_market_crawler.py data/raw/market/
git commit -m "feat: add yfinance market crawler (MSFT, GOOGL)"
git push
```

---

### Task 6: Trends crawler — `pytrends` + circuit breaker (RQ-02, Tier B)

**Files:**
- Create: `src/aicor/sources/trends.py`, `docs/decisions/trends_config.yaml` (provisional, chờ chốt §15.2)
- Test: `tests/integration/test_trends_crawler.py`

**Interfaces:**
- Consumes: `SourceRecord`, `write_sync_log` (Task 3)
- Produces: `fetch_trends(keywords: list[str], geo: str, timeframe: str) -> DataFrame[date, keyword, interest_score]`; `TrendsUnavailable(Exception)` → caller fallback weight (SPEC §7.4); config provisional: keywords `["Microsoft AI", "Azure AI", "Google AI", "Gemini"]`, `geo="US"`, `timeframe="2022-01-01 2026-10-13"`, `search_type="web"` — gắn nhãn `provisional: true`, KHÔNG coi là đã chốt

- [ ] **Step 1: Write the failing test**

```python
def test_trends_circuit_breaker_falls_back():
    with mock_pytrends_raise(UnexpectedMethodException):
        with pytest.raises(TrendsUnavailable):
            fetch_trends(["Microsoft AI"], "US", "2022-01-01 2026-10-13")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_trends_crawler.py -v -m "not live"`
Expected: FAIL

- [ ] **Step 3: Implement `fetch_trends` (single historical query — KHÔNG nối nhiều thang 0–100; mọi exception pytrends → `TrendsUnavailable` + `sync_status=partial`; lưu CSV + `retrieved_at`)**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_trends_crawler.py -v -m "not live"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicor/sources/trends.py docs/decisions/trends_config.yaml tests/integration/test_trends_crawler.py
git commit -m "feat: add pytrends crawler with circuit breaker (provisional config)"
git push
```

---

### Task 7: IR/events crawler — products + events (RQ-02, Tier A)

**Files:**
- Create: `src/aicor/sources/ir.py`, `rubric/v1.yaml` (provisional A/B/C, chờ chốt §15.1)
- Test: `tests/integration/test_ir_crawler.py`, `tests/unit/test_rubric.py`

**Interfaces:**
- Consumes: `SourceRecord` (Task 3)
- Produces: `scrape_ir_blog(feed_url: str) -> list[IrItem(product_name, announcement_date, description, source_url)]`; `classify_abc(item, rubric) -> ("A"|"B"|"C", rationale)`; `review_status in {"pending","reviewed","rejected"}` (§6.3); dedup theo `source_url` chuẩn hóa (không đếm trùng vì nhiều trang)

- [ ] **Step 1: Write the failing test**

```python
def test_rubric_rejects_duplicate_url(ir_items_dup):
    out = dedup_ir_items(ir_items_dup)
    assert len(out) == 1  # SPEC §6.3: không tính trùng vì nhiều trang
    assert classify_abc(out[0], RUBRIC_V1)[0] in ("A", "B", "C")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_ir_crawler.py tests/unit/test_rubric.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `scrape_ir_blog` (regex-first trên RSS/HTML tĩnh 4 blogs §3.3; lưu HTML snapshot vào `data/raw/ir_documents/` — đã ignore, chỉ commit manifest) + `rubric/v1.yaml` provisional (`version: v1-provisional`, A/B/C + ví dụ + quy tắc preview-vs-release) + `classify_abc`/`dedup_ir_items`**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_ir_crawler.py tests/unit/test_rubric.py -v -m "not live"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicor/sources/ir.py rubric/v1.yaml tests/integration/test_ir_crawler.py tests/unit/test_rubric.py
git commit -m "feat: add IR crawler with provisional A/B/C rubric"
git push
```

---

### Task 8: Cleaning + Missing-value policy (Lecture slide 3/5, 4/5; SRC-05)

**Files:**
- Create: `src/aicor/preprocess/cleaning.py`, `src/aicor/preprocess/missing.py`
- Test: `tests/unit/test_cleaning.py`, `tests/unit/test_missing.py`

**Interfaces:**
- Consumes: DataFrames thô từ Tasks 4–7
- Produces: `clean_financial(df) -> df` (ép kiểu, chuẩn `unit_scale`, drop dòng rác); `mark_missing(df, reason_col="reason") -> df` với `value=NULL, status="unavailable"` — KHÔNG fill 0 trừ khi nguồn xác nhận 0 (§6.1); `MISSING_REASONS = {"no_10q_q4_derived_later", "tag_absent", "trends_unavailable", "ir_pending_review", ...}`

- [ ] **Step 1: Write the failing test**

```python
def test_missing_never_zero_filled():
    df = mark_missing(pd.DataFrame({"rd_expense": [None]}), reason_col="reason")
    assert df.loc[0, "rd_expense"] is None and df.loc[0, "status"] == "unavailable"
    assert df.loc[0, "reason"] != ""  # SRC-05: reason bắt buộc
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_cleaning.py tests/unit/test_missing.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `clean_financial` (strip, ép numeric, validate `currency/unit_scale` hiện diện khi có số tiền — §6.2) và `mark_missing` (NULL + status + reason, append `data_quality_log`)**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_cleaning.py tests/unit/test_missing.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicor/preprocess/ tests/unit/test_cleaning.py tests/unit/test_missing.py
git commit -m "feat: add cleaning and NULL-policy missing-value handler"
git push
```

---

### Task 9: Transformation/Reshaping — YTD→Q, DAT-01, units (Lecture slide 3/5; §6.2, §7.2)

**Files:**
- Create: `src/aicor/preprocess/transform.py`
- Test: `tests/unit/test_transform.py`

**Interfaces:**
- Consumes: cleaned financial (Task 8)
- Produces: `ytd_to_quarterly(ytd: dict[str, float]) -> dict[str, float]` (`Q1=3M, Q2=6M−3M, Q3=9M−6M, Q4=FY−9M`); `align_calendar(df) -> df` (thêm `period_end_date`, `calendar_quarter`, `year` — derived Date→parts slide 1/9; join key DAT-01); `normalize_units(df) -> df` (về USD millions)

- [ ] **Step 1: Write the failing test**

```python
def test_q4_never_uses_3m_fact():
    q = ytd_to_quarterly({"3M": 10.0, "6M": 22.0, "9M": 35.0, "FY": 50.0})
    assert q == {"Q1": 10.0, "Q2": 12.0, "Q3": 13.0, "Q4": 15.0}  # Q4 = FY − 9M
    assert align_calendar(msft_fyQ4_row)["calendar_quarter"] == align_calendar(googl_q4_row)["calendar_quarter"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_transform.py -v`
Expected: FAIL

- [ ] **Step 3: Implement 3 hàm trên; `ytd_to_quarterly` raise `DerivationError` khi thiếu `FY` hoặc `9M` (thà NULL theo Task 8 còn hơn đoán)**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_transform.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicor/preprocess/transform.py tests/unit/test_transform.py
git commit -m "feat: add YTD-to-quarterly and calendar-quarter alignment"
git push
```

---

### Task 10: Integration/Join + Dummy + Derived features (Lecture slide 3/5, 5–8/9; §7.1, §8.3)

**Files:**
- Create: `src/aicor/preprocess/integrate.py`, `src/aicor/preprocess/features.py`
- Test: `tests/unit/test_integrate.py`, `tests/unit/test_features.py`

**Interfaces:**
- Consumes: quarterly frames (Task 9), classified IR items (Task 7)
- Produces: `join_panel(msft, googl) -> panel` (join trên `period_end_date`, append-only, không ghi đè — §8.2); `add_company_dummy(panel) -> panel` (`is_msft` 0/1, k−1 dummy slide 5/9); `product_score(counts) -> int` (`3A+2B+1C`, §7.1); `rd_intensity(rd, revenue)`, `capex_intensity(capex, revenue)` (derived kiểu Price/Area slide 3/9); `event_type_dummies(events)` (one-hot, KHÔNG label-encoding — slide 8/9 vì Out là linear non-tree-like)

- [ ] **Step 1: Write the failing test**

```python
def test_product_score_and_dummies():
    assert product_score({"A": 2, "B": 1, "C": 3}) == 3*2 + 2*1 + 1*3
    assert set(event_type_dummies(["funding", "partnership"]).columns) == {"event_funding", "event_partnership"}
    assert "company_id_int" not in join_panel(...)  # cấm label-encoding công ty
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_integrate.py tests/unit/test_features.py -v`
Expected: FAIL

- [ ] **Step 3: Implement 5 hàm trên; mỗi derived ghi `definition, calculation_method, reported_or_derived="derived", proxy, confidence` (§6.1); R&D `proxy=true, confidence="LOW"` (SRC-06)**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_integrate.py tests/unit/test_features.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicor/preprocess/integrate.py src/aicor/preprocess/features.py tests/unit/test_integrate.py tests/unit/test_features.py
git commit -m "feat: add panel join, dummies and derived features"
git push
```

---

### Task 11: Scaling/Normalization + Outlier (Lecture slide 4/5, 5/5; §7.2–§7.3, §7.5)

**Files:**
- Create: `src/aicor/preprocess/scale.py`
- Test: `tests/unit/test_scale.py`

**Interfaces:**
- Consumes: panel + derived (Task 10), `docs/decisions/baseline.yaml` (`z_window: 16`, `trends_norm: minmax_16q`, `ma4q_min_periods: 4`)
- Produces: `ma4q(s, min_periods=4) -> s` (thiếu 1 quý → NULL, §7.2); `minmax_16q(s) -> s` (Trends, window 16Q); `zscore_16q(s) -> (z, status)` (`std=0 → z=0, status="degenerate"`; <16 quý → `status="insufficient_window"` + giá trị vẫn tính kèm cờ hồi cứu §7.3); `flag_outliers(s) -> flags` (IQR trên QoQ-delta; restatement có filing mới = hợp lệ, lỗi parse = noise — slide p16 "outlier vs noise", chỉ flag vào `data_quality_log`, KHÔNG xóa)

- [ ] **Step 1: Write the failing test**

```python
def test_zscore_degenerate_and_ma4q_strict():
    z, st = zscore_16q(pd.Series([5.0] * 16))
    assert (z == 0.0).all() and (st == "degenerate").all()  # §7.5
    assert ma4q(pd.Series([1.0, 2.0, 3.0])).isna().all()  # <4 quý → NULL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_scale.py -v`
Expected: FAIL

- [ ] **Step 3: Implement 4 hàm trên (rolling window 16, `ddof=1`; công thức tính toán `In/Out/E` thuộc phase Compute — KHÔNG làm ở task này)**

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_scale.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/aicor/preprocess/scale.py docs/decisions/baseline.yaml tests/unit/test_scale.py
git commit -m "feat: add MA4Q, min-max, rolling z-score and outlier flags"
git push
```

---

### Task 12: GitHub Actions crawl tự động + xác minh end-to-end

**Files:**
- Create: `.github/workflows/crawl-sec.yml`, `crawl-market.yml`, `crawl-trends.yml`, `crawl-ir.yml`, `validate.yml`
- Test: `tests/integration/test_pipeline_e2e.py` (fixture → chạy full 8 bước §9 trên mẫu 4 quý, assert `analysis`-ready panel + manifest đầy đủ)

**Interfaces:**
- Consumes: toàn bộ Tasks 2–11
- Produces: 4 cron workflows (market sau phiên `0 13-20 * * 1-5`; sec `0 */6 * * *`; trends `0 */12 * * *`; ir `0 2 * * *` — PIPE-01) + `validate.yml` (chạy trên mọi push: `pytest -m "not live"`, FR_T01/DQ_T04 gates); mỗi run commit data (`manifest.csv`, `*.csv` staged) về repo qua `GITHUB_TOKEN`; failure 1 nguồn → `partial`, không rollback nguồn khác (NFR-04)

- [ ] **Step 1: Write the failing test**

```python
def test_e2e_panel_provenance_complete(sample_4q):
    panel = run_pipeline(sample_4q)  # Collect→…→Monitor (§9) trên fixture
    assert panel["source_id"].notna().all()  # SRC-03, NFR-02
    assert (panel["sync_status"] == "partial").any()  # 1 nguồn fail giả lập → partial, data còn lại nguyên (NFR-04)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_pipeline_e2e.py -v`
Expected: FAIL (`run_pipeline` chưa tồn tại)

- [ ] **Step 3: Implement `run_pipeline` (điều phối Collect→Archive→Validate→Normalize→Transform→Publish→Monitor theo §9; Validate gồm FR_T01 21-quý + DQ_T04 Assets=L+E) và 5 workflow YAML (checkout → `uv sync` → crawl → validate → `git commit data/ || echo no-change` → push; secrets: chỉ `SEC_USER_AGENT` qua env — NFR-06)**

- [ ] **Step 4: Run full suite offline + trigger thủ công 1 workflow**

Run: `uv run pytest -m "not live" -q`
Expected: toàn PASS. Sau đó trên GitHub: Actions → `crawl-sec` → Run workflow → log xanh, commit data mới xuất hiện

- [ ] **Step 5: Commit + tag phase**

```bash
git add .github/ src/aicor/pipeline/ tests/integration/test_pipeline_e2e.py
git commit -m "feat: automate crawlers with GitHub Actions schedules"
git tag crawl-phase-v1 && git push origin main --tags
```

---

## Self-Review

1. **Spec coverage:** SRC-01→Task 3 (tier validator); SRC-03→Tasks 3+12 (source_id bắt buộc); SRC-04→Task 4 (dùng SEC) + §6.2; SRC-05/07→Task 8; SRC-06→Task 10 (proxy/confidence); SRC-08/09→Task 5; DAT-01→Task 9; §6.2→Task 4; §6.3→Task 7; §6.4→Task 6; §6.5→Task 7; §6.6→Task 5; §6.7→Tasks 3+12; §7.1→Task 10; §7.2/7.3/7.5→Task 11; §7.4 weights→ghi config Task 11 (compute E ở phase sau — KHÔNG thiếu vì phase này chỉ crawl+preprocess); §8.1→Tasks 3,8–11 (bảng 2,3,4,5,6,7,8,9-phần feature,11,12); PIPE-01/02→Task 12; NFR-01→manifest+SHA (Tasks 3–4); NFR-02→Task 12; NFR-03→`baseline.yaml`+`rubric/v1.yaml` versioned; NFR-04→Task 12; NFR-06→Tasks 2+12; NFR-07→Tasks 2+4; NFR-08→chia module sources/preprocess/pipeline. Gap đã ghi nhận: `In/Out/E` compute + provenance JSON + dashboard thuộc phase sau.
2. **Step scan:** mỗi step 1 action + kết quả check được; không có dòng TBD; không transcript body.
3. **Type consistency:** `SourceRecord`/`write_sync_log`/`sha256_file` (T3) dùng nhất quán ở T4–T7, T12; `resolve_metric`, `fetch_*`, `ytd_to_quarterly`, `align_calendar`, `product_score`, `ma4q`, `zscore_16q`, `run_pipeline` mỗi tên định nghĩa 1 lần, gọi lại đúng tên.
4. **Review Focus:** 5 dòng đều có test ở task sở hữu (T9, T4, T6, T9, T12).
5. **Proportion:** plan ~250 dòng cho ~40 file triển khai — là plan, không phải transcript.
