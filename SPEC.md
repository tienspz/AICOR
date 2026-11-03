# ĐV-ĐR — Đặc tả yêu cầu hệ thống (System Requirements Specification — SRS)

| Thuộc tính | Giá trị |
| --- | --- |
| Mã tài liệu | ĐV-ĐR-SRS |
| Trạng thái | Baseline — đã khóa phạm vi công ty; bổ sung lớp nowcast/forecast có kiểm soát (Phase 2.5) |
| Tên đề tài | **Đối chiếu đầu tư R&D với tín hiệu kết quả AI** |
| Phạm vi | Microsoft và Alphabet · Theo quý từ 2022 |
| Tên tiếng Anh | **Comparing R&D Investment with AI Outcome Signals at Microsoft and Alphabet: A Quarterly Analysis since 2022** (ĐV-ĐR) |
| Hệ thống | **ĐV-ĐR** — Hệ thống Nghiên cứu Đầu vào – Đầu ra AI (AI Input–Output Research System) |
| Đối tượng so sánh | Microsoft Corporation (MSFT) và Alphabet Inc. (GOOGL/GOOG) |
| Đơn vị phân tích chính | Công ty × Quý (xem DAT-01 về căn chỉnh quý lịch) |
| Khoảng dữ liệu chính | 2021-Q1 → 2026-Q2: 22 quý/công ty, 44 quan sát; 2021 là warm-up cho MA4Q; z16Q đủ cửa sổ từ 2024-Q4 (7 cửa sổ/công ty), 15 quý đầu bị flag; phân tích chính từ 2022 |


### Quy ước dịch

Tên trường dữ liệu, tên bảng, mã yêu cầu, tên tier, giá trị trạng thái (`ROBUST`, `SENSITIVE`, `NULL`…) và thuật ngữ kỹ thuật chuẩn (CapEx, FCF, lag, z-score…) giữ nguyên tiếng Anh để khớp mã nguồn và cơ sở dữ liệu.

### Động từ chỉ mức bắt buộc

| Từ dùng | Mức | Tương ứng tiếng Anh |
| --- | --- | --- |
| "phải" | Bắt buộc | shall / must |
| "nên" | Khuyến nghị | should |
| "có thể" | Tùy chọn | may |

Mọi điều khoản có mã yêu cầu mặc định là **bắt buộc**, trừ khi ghi rõ mức khác.

---

## 0. Ghi chú hợp nhất phiên bản

Tài liệu này hợp nhất hai bản SPEC trước đó của dự án, vốn đại diện cho hai mô hình phân tích khác nhau cho cùng một hệ thống, không phải hai bản vá nối tiếp nhau.

**Quyết định 1 — Khóa phạm vi công ty: Microsoft và Alphabet.** Hai bản trước có mâu thuẫn: một bản mặc định Microsoft/Alphabet, bản còn lại ghi nhận khả năng đổi sang Microsoft/OpenAI/Anthropic nhưng chưa chốt. Quyết định này khóa về **Microsoft và Alphabet**, vì lý do kỹ thuật: mô hình định lượng dựa trên R&D/CapEx từ SEC (Tier S) chỉ đứng vững khi cả hai đối tượng đều là công ty niêm yết có báo cáo tài chính định kỳ. OpenAI và Anthropic là công ty tư nhân, chỉ có dữ liệu sự kiện gọi vốn rời rạc, không đủ để nuôi một chuỗi quý liên tục cho `In`. Hướng phân tích quan hệ chiến lược Microsoft–OpenAI–Anthropic được ghi nhận là hướng mở rộng tương lai, nằm ngoài phạm vi bản này.

**Quyết định 2 — Hệ quả của Quyết định 1: đơn giản hóa công thức `In`.** Vì cả hai công ty đều niêm yết và đều công bố R&D trên hồ sơ SEC, `In` dùng chung một công thức đối xứng cho cả hai công ty (`In = z(R&D theo quý)`, Tier S), không cần một bảng ước tính chi tiêu AI độ tin cậy thấp riêng cho công ty không có báo cáo tài chính. Điều này đóng luôn một vấn đề mở còn tồn đọng ở bản trước đó.

**Quyết định 3 — Giữ mô hình phân tích đơn giản (`E = Out − In`), không khôi phục mô hình lag/efficiency/event-study.** Mô hình lag analysis (0–4 quý) kết hợp bốn công thức hiệu quả, event study với abnormal return, regime detection và phân tích độ nhạy trên nhiều chiều cùng lúc là khối lượng công việc vượt quá khả năng hoàn thành của một nhóm ba người trong một học kỳ. Quyết định này là chủ đích kỹ thuật, không phải bỏ sót; mô hình `E = Out − In` với Product Score, trung bình động 4 quý và z-score được giữ làm lõi phân tích. Lớp nowcast/forecast ở Quyết định 5 là module bổ sung tách biệt, không khôi phục mô hình lag/event-study đa chiều làm lõi.

**Quyết định 4 — Bổ sung lại tính nghiêm ngặt kiểu CMU bị thiếu ở bản trước:** mô hình Tier nguồn dữ liệu (S/A/B/R), hệ thống mã yêu cầu có thể truy vết, ma trận xác minh (Verification Matrix) và Định nghĩa Hoàn thành (Definition of Done).

**Quyết định 5 — Bổ sung lớp nowcast/forecast có kiểm soát (lớp dự báo ĐV-ĐR), không thay đổi lõi mô tả.** ĐV-ĐR mở rộng từ đo lường hồi cứu sang:
- **Nowcast** `E` của quý hiện tại trước khi 10-Q được nộp (`h = 0`).
- **Forecast** các thành phần `R&D`, `Product MA4Q`, `Trends MA4Q` (hoặc `E`/`Out` nếu config chọn) cho quý kế tiếp (`h = 1`), kèm khoảng tin cậy 80%/95%.
- **Alert** khi interval 80% của `E` cắt 0, `E` forecast dưới ngưỡng, hoặc nowcast lệch khỏi giá trị `E` đã công bố gần nhất.
- **Driver attribution** để giải thích yếu tố đóng góp.

Ràng buộc kỹ thuật: baseline naive/AR(1); model chính là Ridge/Elastic Net/Bayesian Ridge; **không dùng Deep Learning** ở baseline vì `N` nhỏ (tối đa 44 pooled, 14 nếu target `E` trực tiếp); mọi kết quả phải qua rolling-origin backtest, point-in-time guard, model card và nhãn "experimental". Đây là lớp mở rộng, không thay thế `E` mô tả và không phải khuyến nghị đầu tư. Các hướng **causal event study** và **LLM event intelligence** được ghi nhận là mở rộng tùy chọn, không thuộc baseline (mục 15).

---

## 1. Giới thiệu

### 1.1 Mục đích

> **Tên đề tài nghiên cứu:**
> - **Tiếng Việt:** *Đối chiếu đầu tư R&D với tín hiệu kết quả AI*
> - **Phạm vi:** *Microsoft và Alphabet · Theo quý từ 2022*
> - **Tiếng Anh:** *Comparing R&D Investment with AI Outcome Signals at Microsoft and Alphabet: A Quarterly Analysis since 2022* (ĐV-ĐR)

ĐV-ĐR là hệ thống nghiên cứu theo quý, so sánh **mức đầu vào liên quan đến AI** (`In`) với **các chỉ báo đầu ra AI** (`Out`) của Microsoft và Alphabet. Kết quả là điểm tương đối `E = Out − In`, dùng để quan sát xu hướng trong lịch sử dữ liệu của từng công ty và kiểm tra độ nhạy khi thay đổi trọng số.

Từ bản cập nhật này, ĐV-ĐR bổ sung **lớp nowcast/forecast có kiểm soát**: ước lượng `E` của quý hiện tại trước khi 10-Q được nộp (nowcast) và dự báo `E`/`Out` một quý tới (forecast), kèm khoảng tin cậy, cảnh báo và driver attribution. Đây là lớp mở rộng tách biệt với lõi mô tả; kết quả được gắn nhãn thử nghiệm và không phải khuyến nghị đầu tư.

`E` không phải ROI, lợi nhuận, tỷ suất sinh lời hay bằng chứng nhân quả.

ĐV-ĐR không cố ước tính một con số kế toán ẩn gọi là "AI Investment", vì báo cáo tài chính của cả hai công ty không có dòng kế toán chuẩn hóa theo quý mang tên đó. Hệ thống tách bạch bốn loại dữ liệu: dữ liệu tài chính đã báo cáo, chỉ số AI công ty công bố rõ ràng, đặc trưng tài chính suy ra (derived), và biến đại diện cho đầu tư AI (proxy, được gán nhãn rõ).

### 1.2 Cơ sở xây dựng đặc tả

Đặc tả theo cấu trúc requirements engineering chịu ảnh hưởng từ CMU/SEI (Carnegie Mellon Software Engineering Institute): xác định yêu cầu, phân tích yêu cầu, biểu diễn yêu cầu, truyền đạt yêu cầu, tiêu chí và quy trình chấp nhận. ĐV-ĐR được xem là một **hệ thống nghiên cứu**, không chỉ là một dashboard và cũng không chỉ là một mô hình dự báo.

Tham chiếu phương pháp (Tier R, không dùng làm dữ liệu phân tích):

| Tài liệu | URL |
| --- | --- |
| CMU/SEI — Software Requirements | `https://www.sei.cmu.edu/library/software-requirements/` |
| CMU/SEI — Software Specification: A Framework | `https://www.sei.cmu.edu/library/software-specification-a-framework/` |
| CMU/SEI — A Requirement Specification Language for AADL | `https://www.sei.cmu.edu/library/a-requirement-specification-language-for-aadl-2/` |

> **Lưu ý kiểm chứng:** ba URL trên chưa được xác minh lại trong bản hợp nhất này. Cần mở thủ công, ghi `access_date` trước khi nộp.

### 1.3 Phạm vi

#### 1.3.1 Trong phạm vi

**Microsoft**

```text
Company: Microsoft Corporation
Ticker: MSFT
Exchange: NASDAQ
Fiscal year end: June 30
```

**Alphabet**

```text
Company: Alphabet Inc.
Tickers: GOOGL / GOOG
Exchange: NASDAQ
Fiscal year end: December 31
```

Phạm vi hoạt động của hệ thống gồm: thu thập dữ liệu tài chính/R&D, dữ liệu sản phẩm AI, Google Trends, sự kiện liên quan và giá cổ phiếu; lưu trữ append-only kèm metadata nguồn; làm sạch và chuẩn hóa theo quý; tính Product Score, MA4Q, z-score, `In`, `Out`, `E` và các kịch bản trọng số; hiển thị dashboard; ghi log đồng bộ và chất lượng dữ liệu.

Từ Phase 2.5, phạm vi bổ sung **lớp dự báo ĐV-ĐR**: **nowcast** quý hiện tại, **forecast** 1 quý tới cho `E`/`Out`, khoảng tin cậy 80%/95%, **alert** theo ngưỡng và **driver attribution**; tất cả chỉ dùng dữ liệu point-in-time và được gắn nhãn thử nghiệm.

#### 1.3.2 Ngoài phạm vi

* Giao dịch tự động; dự báo giá cổ phiếu; khuyến nghị mua/bán; dự báo xa hơn nowcast quý hiện tại hoặc forecast 1 quý tới, hoặc cho công ty ngoài phạm vi.
* Tính ROI/lợi nhuận đầu tư thực tế từ `E`.
* Khẳng định quan hệ nhân quả.
* Tự tạo số ước tính không có nguồn hoặc không ghi rõ phương pháp.
* Xếp hạng hiệu suất tuyệt đối giữa hai công ty dựa trên `E` như một thang đo đã hiệu chỉnh tương đương.
* Cào dữ liệu trái điều khoản nguồn hoặc vượt giới hạn truy cập (robots.txt, rate limit).
* Phân tích công ty tư nhân (OpenAI, Anthropic) hoặc quan hệ đầu tư/chiến lược giữa các công ty — ghi nhận là hướng mở rộng tương lai (xem mục 0).
* Mô hình lag analysis đa chiều, event study, regime detection, scenario analysis như đặc tả ở bản SPEC trước — không dùng làm lõi; lõi là `E = Out − In` (xem mục 0, Quyết định 3). Lớp nowcast/forecast ở mục 7.6 là module bổ sung, không phải các mô hình này.
* Ước tính tài chính của công ty chưa niêm yết; ước tính của giới phân tích trình bày như kết quả thực tế; bài báo/tin tức dùng thay báo cáo tài chính; tuyên bố mạng xã hội chưa kiểm chứng; con số "chi tiêu AI" chung chung không nguồn.

### 1.4 Định nghĩa, thuật ngữ

| Thuật ngữ | Ý nghĩa |
| --- | --- |
| AI Investment Proxy | Biến đại diện, gán nhãn rõ, dùng khi công ty không công bố trực tiếp khoản đầu tư AI (ở đây là R&D). |
| CapEx | Chi tiêu vốn (capital expenditure). |
| FCF | Dòng tiền tự do, `CFO − CapEx`. |
| `In` | Chỉ số đầu vào chuẩn hóa, `z(R&D theo quý)`. |
| `Out` | Chỉ số đầu ra chuẩn hóa, kết hợp Product Score và Google Trends. |
| `E` | Điểm tương đối, `Out − In`. |
| Nowcast | Ước lượng `E` của quý hiện tại trước khi báo cáo quý được công bố, dùng dữ liệu tần suất cao có sẵn tại thời điểm ước lượng (`h = 0`). |
| Forecast | Dự báo `E`/`Out` (hoặc các thành phần `R&D`, `Product MA4Q`, `Trends MA4Q`) cho quý kế tiếp (`h = 1`), kèm khoảng tin cậy. |
| Forecast origin / target | Quý xuất phát (feature cutoff) và quý được dự báo (target); feature chỉ dùng dữ liệu có sẵn tại `as_of_date`. |
| As-of date | Mốc cắt dữ liệu để bảo đảm không dùng thông tin tương lai. |
| Prediction interval | Khoảng tin cậy của forecast, tối thiểu 80% và 95%. |
| Backtest | Kiểm định rolling-origin trên dữ liệu lịch sử, chỉ dùng thông tin có sẵn tại từng mốc. |
| Directional accuracy | Tỷ lệ dự báo đúng chiều thay đổi của target so với kỳ trước. |
| Model card | Tài liệu mô tả mục tiêu, feature, dữ liệu huấn luyện, metric, giới hạn và artifact hash của model. |
| Alert | Cảnh báo khi nowcast/forecast vượt ngưỡng hoặc vi phạm rule đã cấu hình. |
| Driver attribution | Phân rã đóng góp của từng feature vào nowcast/forecast; không phải quan hệ nhân quả. |
| Product Score | Điểm sản phẩm AI theo quý, tính từ rubric A/B/C. |
| MA4Q | Trung bình động 4 quý. |
| z-score | Chuẩn hóa `(x − mean(x)) / std(x)`. |
| Tier S/A/B/R | Bậc tin cậy của nguồn dữ liệu (mục 3.1). |
| Reported/Derived/Proxy | Ba trạng thái của một chỉ số: báo cáo trực tiếp / tính từ chỉ số khác / biến đại diện gián tiếp. |
| SEC EDGAR, XBRL | Hệ thống nộp hồ sơ điện tử của Ủy ban Chứng khoán Hoa Kỳ và định dạng dữ liệu tài chính có cấu trúc. |
| IR | Investor Relations, trang quan hệ nhà đầu tư của công ty. |

### 1.5 Hệ thống mã yêu cầu

| Tiền tố | Nhóm | Mục |
| --- | --- | --- |
| RQ | Câu hỏi nghiên cứu | 2 |
| SRC | Nguồn và độ tin cậy | 3 |
| DAT | Yêu cầu dữ liệu đầu vào | 6 |
| CALC | Quy tắc tính toán | 7 |
| DB | Data model/lưu trữ | 8 |
| PIPE | Pipeline thu thập/xử lý | 9 |
| DSH | Dashboard | 10 |
| FCST | Nowcast, forecast, alert, model validation | 6.8, 7.6, 8–11, 13 |
| NFR | Yêu cầu phi chức năng | 11 |

Mỗi yêu cầu có thuộc tính tối thiểu: mã, nội dung, căn cứ khi không hiển nhiên, cách xác minh (Phụ lục A).

---

## 2. Mục tiêu và câu hỏi nghiên cứu

### 2.1 Mục tiêu

* Thu thập dữ liệu công khai theo quý từ 2021-Q1 đến 2026-Q2 (22 quý/công ty; 2021 là warm-up cho MA4Q; z16Q đủ cửa sổ từ 2024-Q4; phân tích chính từ 2022), cho Microsoft và Alphabet.
* Chuẩn hóa dữ liệu đầu vào và lưu lại nguồn để kiểm chứng.
* Tính Product Score, MA4Q, z-score, `In`, `Out`, `E`.
* Hiển thị xu hướng theo thời gian, timeline sự kiện, và độ nhạy với các bộ trọng số.
* Cung cấp trạng thái đồng bộ và dấu vết dữ liệu để người dùng kiểm tra chất lượng kết quả.
* Nowcast `E` quý hiện tại trước khi 10-Q được nộp, chỉ dùng dữ liệu có sẵn tại `as_of_date`.
* Forecast `E`/`Out` 1 quý tới với khoảng tin cậy 80%/95%, có backtest và model card.
* Phát alert khi interval 80% của `E` cắt 0, `E` forecast dưới ngưỡng, hoặc nowcast lệch khỏi giá trị publish gần nhất.
* Giải thích yếu tố đóng góp (driver attribution) mà không khẳng định nhân quả.

### 2.2 Câu hỏi nghiên cứu

| Mã | Câu hỏi |
| --- | --- |
| RQ-01 | Theo từng quý, mức đầu vào R&D liên quan đến AI của Microsoft và Alphabet thay đổi thế nào? |
| RQ-02 | Đầu ra AI (sản phẩm công bố, mức chú ý thị trường qua Trends) thay đổi thế nào theo cùng chu kỳ? |
| RQ-03 | Điểm tương đối `E = Out − In` của từng công ty biến động ra sao theo thời gian? |
| RQ-04 | Kết luận về `E` có đứng vững khi đổi trọng số giữa Product Score và Trends không (0.6/0.4, 0.5/0.5, 0.7/0.3)? |
| RQ-05 | Nowcast `E` quý hiện tại chính xác đến đâu khi chỉ dùng dữ liệu có sẵn trước khi 10-Q được nộp? |
| RQ-06 | Forecast `E`/`Out` 1 quý tới có beat baseline naive/AR(1) trong rolling-origin backtest không, và khoảng tin cậy có đủ độ phủ? |
| RQ-07 | Alert có phát đúng thời điểm và có tỷ lệ false positive chấp nhận được không? |

### 2.3 Những câu hỏi ĐV-ĐR không trả lời

* Công ty nào đầu tư AI sinh lời nhất.
* Một khoản đầu tư cụ thể tạo ra chính xác bao nhiêu kết quả.
* Đầu tư AI là nguyên nhân làm đầu ra hoặc giá cổ phiếu tăng.
* Dự báo `E` xa hơn nowcast quý hiện tại hoặc forecast 1 quý tới, dự báo giá cổ phiếu, hoặc dự báo cho công ty ngoài phạm vi.
* Khuyến nghị mua, bán hoặc phân bổ vốn đầu tư thực tế.
* Khái quát kết quả cho toàn bộ ngành AI hoặc cho công ty ngoài phạm vi (mục 1.3.2).

---

## 3. Nguồn dữ liệu và độ tin cậy

### 3.1 Mô hình độ tin cậy nguồn

**SRC-01.** Mọi nguồn phải được gán một bậc tin cậy.

**Tier S — Nguồn pháp lý/tài chính gốc.** SEC EDGAR, SEC 10-Q, SEC 10-K, SEC XBRL. Dùng cho Revenue, R&D, CapEx, Operating Income, Net Income, CFO, Assets, Shares, EPS, dữ liệu theo phân khúc.

**Tier A — Nguồn gốc từ công ty.** Thông cáo kết quả kinh doanh, bài thuyết trình nhà đầu tư, công bố IR chính thức, blog/changelog sản phẩm chính thức. Dùng cho Azure Growth, Microsoft Cloud Growth, Google Cloud Growth, thông tin sản phẩm AI.

**Tier B — Dữ liệu thị trường.** Giá cổ phiếu, khối lượng giao dịch. Trường bắt buộc: `date, open, high, low, close, adjusted_close, volume`.

**SRC-02.** Dữ liệu Tier B **không được** thay thế nguồn SEC/công ty cho các biến kế toán.

**Tier R — Tham chiếu phương pháp.** Tài liệu CMU/SEI (mục 1.2). Không dùng làm dữ liệu phân tích, nằm ngoài `source_registry`.

### 3.2 Yêu cầu Source Registry

**SRC-03.** Mọi điểm dữ liệu dùng trong tầng phân tích phải truy vết được đến một nguồn, theo schema mục 8.1 (`source_registry`).

```yaml
source_id: MSFT_SEC_10Q_2026Q3
company: Microsoft
metric: Revenue
source_type: SEC_10Q
source_tier: S
source_url: https://www.sec.gov/Archives/edgar/data/789019/000119312526191507/msft-20260331.htm
reporting_period: 2026-03-31
primary_or_secondary: primary
verification_status: verified
```

### 3.3 Nguồn chuẩn (canonical sources)

| Nguồn | URL | Tier |
| --- | --- | --- |
| Microsoft — SEC EDGAR | `https://www.sec.gov/edgar/browse/?CIK=789019` | S |
| Microsoft — SEC Company Facts (XBRL API) | `https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json` | S |
| Microsoft — Investor Relations | `https://www.microsoft.com/en-us/investor/` | A |
| Microsoft — Blog | `https://blogs.microsoft.com/blog/` | A |
| Azure — Blog | `https://azure.microsoft.com/en-us/blog/` | A |
| Alphabet — SEC EDGAR | `https://www.sec.gov/edgar/browse/?CIK=1652044` | S |
| Alphabet — Investor Relations | `https://abc.xyz/investor/` | A |
| Google — Blog | `https://blog.google/` | A |
| Google Cloud — Blog | `https://cloud.google.com/blog` | A |
| Google — Research Blog | `https://research.google/blog/` | A |
| Microsoft — Research | `https://www.microsoft.com/en-us/research/` | A |
| Google Trends | `https://trends.google.com/trends/` | B |
| Yahoo Finance — MSFT | `https://finance.yahoo.com/quote/MSFT/history/` | B |
| Yahoo Finance — GOOGL | `https://finance.yahoo.com/quote/GOOGL/history/` | B |

> **Lưu ý kiểm chứng:** URL hồ sơ SEC cụ thể theo từng quý (ví dụ filing của FY26 Q3) phải được lấy lại tại thời điểm crawl thật, không hard-code một filing cố định trong tài liệu này — số thứ tự accession thay đổi theo từng kỳ nộp báo cáo.

> **Nguồn đã đánh giá và loại khỏi phạm vi:** trang `nasdaq.com/market-activity/stocks/{msft,googl}` đã được kiểm tra và loại khỏi vai trò nguồn dữ liệu, vì (a) dữ liệu chỉ render bằng JavaScript phía client, không có trong HTML gốc; (b) `robots.txt` của Nasdaq chặn tường minh `/api/v1/*`, là tầng mà trang web dùng để tải dữ liệu đó. Dữ liệu giá cổ phiếu dùng Yahoo Finance (`yfinance`) theo SRC-04.

### 3.4 Ma trận nguồn dữ liệu

| Dữ liệu | Microsoft | Alphabet | Tier |
| --- | --- | --- | --- |
| Revenue, R&D, CapEx, Operating Income, CFO | SEC 10-Q/10-K | SEC 10-Q/10-K | S |
| Azure / Microsoft Cloud Growth | Microsoft IR | N/A | A |
| Google Cloud Growth | N/A | Alphabet IR | A |
| Sản phẩm AI | Blog/changelog chính thức | Blog/changelog chính thức | A |
| Google Trends | Google Trends | Google Trends | B |
| Giá cổ phiếu | Yahoo Finance | Yahoo Finance | B |
| Filing date | SEC | SEC | S |

### 3.5 Quy tắc chọn nguồn, dữ liệu thiếu và mức tin cậy

**SRC-04 — Quy tắc chọn nguồn.**

```text
IF SEC chứa chỉ số
    DÙNG SEC
ELSE IF nguồn chính thức công ty chứa chỉ số
    DÙNG nguồn công ty
ELSE
    tìm nguồn sơ cấp chất lượng cao hơn
ELSE
    đánh dấu chỉ số không khả dụng
```

Hệ thống **không được bịa giá trị** chỉ để bảng dữ liệu đầy đủ.

**SRC-05 — Dữ liệu thiếu.** `value = NULL`, `status = unavailable`, `reason` ghi rõ lý do. Không điền bằng ước tính của giới phân tích trừ khi tạo riêng bộ dữ liệu tách biệt và gán nhãn rõ.

**SRC-06 — Mức tin cậy.**

| Mức | Điều kiện | Ví dụ |
| --- | --- | --- |
| HIGH | Báo cáo trực tiếp bởi SEC hoặc thông cáo chính thức | Revenue từ 10-Q |
| MEDIUM | Suy ra từ dữ liệu nguồn tin cậy cao | `CapEx / Revenue` |
| LOW | Biến đại diện gián tiếp | R&D làm proxy đầu tư AI |

**SRC-07 — Chỉ dùng dữ liệu thật, thu thập được bằng chương trình.** Không dùng dữ liệu giả/mock/ước tính không dẫn chứng. Biến không có nguồn thật lấy về được thì loại khỏi phạm vi, không tạo giá trị thay thế. Một quan sát thiếu ghi `NULL` theo SRC-05. Mỗi giá trị phải truy vết được đến `source_id`.

### 3.6 Dữ liệu thị trường: nhà cung cấp và benchmark

**SRC-08 — Nhà cung cấp.** Yahoo Finance (Tier B), qua thư viện `yfinance`, cho cả MSFT và GOOGL.

* Lý do chọn: miễn phí, không cần đăng ký, có `adjusted_close`.
* Hạn chế: không phải nguồn chính thức, điều khoản dành cho mục đích cá nhân/học tập, dữ liệu có thể được điều chỉnh về sau.

**SRC-09 — Tái lập.** Tải dữ liệu một lần, lưu CSV gốc vào raw data layer, ghi `access_date` và mã cổ phiếu vào `source_registry`. Không tự tải lại mỗi lần chạy.

---

## 4. Người dùng mục tiêu

| Nhóm | Nhu cầu chính |
| --- | --- |
| Reviewer (giảng viên, người chấm) | Chọn một con số trên dashboard, truy vết đến nguồn, tái lập kết quả |
| Người quan tâm xu hướng đầu tư AI của doanh nghiệp | Xem so sánh, độ nhạy; đọc kết luận kèm giả định |
| Người theo dõi doanh nghiệp trước báo cáo quý | Xem nowcast/forecast `E` kèm khoảng tin cậy, hiểu lý do cảnh báo, không dùng như khuyến nghị đầu tư |
| Nhóm R&D | Tham khảo xu hướng công bố sản phẩm và dữ liệu công khai |
| Kỹ sư dữ liệu (thành viên nhóm) | Nạp dữ liệu, kiểm tra chất lượng, chạy lại pipeline |

---

## 5. Ràng buộc và giả định

* Chỉ dùng dữ liệu công bố công khai, thu thập hợp lệ theo SRC-07.
* SEC là nguồn tài chính chuẩn khi có xung đột với IR.
* Chuỗi dữ liệu hiện có 22 quý/công ty (44 quan sát), từ 2021-Q1 đến 2026-Q2; 2021 là warm-up cho MA4Q; z16Q chỉ có 7 cửa sổ đủ/công ty (14 pooled) từ 2024-Q4, 15 quý đầu bị flag; phân tích chính từ 2022. Đây vẫn là giới hạn cố hữu.
* Microsoft có năm tài chính kết thúc 30/6, Alphabet kết thúc 31/12; mọi so sánh chéo phải qua căn chỉnh quý lịch (DAT-01).
* Hồ sơ SEC EDGAR và trang IR khả dụng trong suốt thời gian thực hiện; SEC yêu cầu client khai báo User-Agent phù hợp.
* Với 44 quan sát (và chỉ 14 pooled cho z16Q), số quan sát hiệu dụng nhỏ; kết quả phải trình bày kèm giới hạn cỡ mẫu.
* Lớp nowcast/forecast chỉ dùng mô hình ít tham số; **không dùng Deep Learning** ở baseline vì dữ liệu chưa đủ.
* Mọi backtest/nowcast phải dùng dữ liệu point-in-time; không dùng thông tin công bố sau `as_of_date`.
* Forecast/nowcast là thử nghiệm, không phải khuyến nghị đầu tư; phải hiển thị khoảng tin cậy và model version.

---

## 6. Yêu cầu dữ liệu đầu vào

### 6.1 Nguyên tắc chung

* Phạm vi thời gian: 2021-Q1 đến 2026-Q2; 2021 là warm-up cho MA4Q; z16Q đủ cửa sổ từ 2024-Q4 (7 cửa sổ/công ty), 15 quý đầu bị flag; phân tích chính từ 2022.
* Lưu giá trị gốc, giá trị chuẩn hóa, đơn vị, kỳ và URL nguồn tách biệt.
* Không thay dữ liệu thiếu bằng `0` trừ khi nguồn xác nhận giá trị thực bằng 0.
* Không trộn số liệu theo quý với số liệu lũy kế nếu không có quy tắc chuyển đổi rõ ràng.
* Mọi giá trị derived phải có phương pháp, nguồn và mức tin cậy.
* Lưu `filing_date`/`published_at` và `retrieved_at` riêng biệt.
* Mỗi dữ liệu đầu vào gắn `company_id`.
* Với nowcast/forecast, mỗi bản ghi phải có `available_at` (thời điểm dữ liệu thực sự có sẵn) và `vintage_id`; xem mục 6.8.

**DAT-01 — Căn chỉnh quý lịch.** Microsoft và Alphabet có năm tài chính lệch nhau. Hệ thống phải lưu `period_end_date` làm khóa so sánh chéo, lưu `fiscal_period` chỉ để hiển thị/đối chiếu nguồn, và khi so sánh hai công ty, ghép theo quý lịch (calendar quarter) suy ra từ `period_end_date`.

### 6.2 Financial/R&D data

| Trường | Kiểu | Bắt buộc | Ý nghĩa |
| --- | --- | --- | --- |
| `company_id` | string | Có | Khóa công ty |
| `fiscal_year`, `fiscal_quarter` | integer, string | Có | Kỳ tài chính của nguồn |
| `period_start`, `period_end` | date | Có | Ngày bắt đầu/kết thúc kỳ |
| `revenue` | decimal/null | Nên có | Doanh thu, bối cảnh |
| `rd_expense` | decimal/null | Theo nguồn | Chi phí R&D; không đồng nghĩa chi tiêu AI |
| `capex` | decimal/null | Theo nguồn | Chi tiêu vốn, proxy phụ (tùy chọn, mục 7.4) |
| `currency`, `unit_scale` | string | Có nếu có số tiền | Đơn vị tiền tệ, thang đơn vị |
| `filing_date` | date/null | Nên có | Ngày filing công bố |
| `source_url`, `source_document_id` | string | Có / Nên có | Truy vết nguồn |
| `retrieved_at` | datetime | Có | Thời điểm ĐV-ĐR lấy dữ liệu |

Nếu báo cáo trình bày số lũy kế từ đầu năm (YTD), phải chuyển thành số quý độc lập bằng phép trừ các kỳ lũy kế phù hợp, và lưu phương pháp chuyển đổi. Quý 4 không có 10-Q riêng; lấy số cả năm từ 10-K trừ số 9 tháng.

### 6.3 Dữ liệu sản phẩm AI

Mỗi bản ghi đại diện cho một sản phẩm hoặc lần công bố/cập nhật được rubric chấp nhận.

| Trường | Kiểu | Bắt buộc | Ý nghĩa |
| --- | --- | --- | --- |
| `product_event_id`, `company_id` | string | Có | Khóa bản ghi, công ty công bố |
| `product_name` | string | Có | Tên sản phẩm/tính năng |
| `announcement_date` | date | Có nếu xác định được | Ngày công bố |
| `description`, `feature_summary` | string/null | Nên có | Mô tả, tóm tắt tính năng AI |
| `category_abc` | enum/null | Sau phân loại | A, B hoặc C theo rubric |
| `category_rationale` | string/null | Nên có | Lý do phân loại |
| `source_url` | string | Có | Trang công bố gốc |
| `review_status` | enum | Có | `pending`, `reviewed`, `rejected` |
| `retrieved_at` | datetime | Có | Thời điểm thu thập |

Không tính một sản phẩm trùng lặp nhiều lần chỉ vì xuất hiện trên nhiều trang. Quy tắc xử lý bản cập nhật, preview, phát hành thương mại và bài blog lặp lại phải được ghi trong rubric (mục 15).

### 6.4 Google Trends

| Trường | Kiểu | Bắt buộc | Ý nghĩa |
| --- | --- | --- | --- |
| `keyword`, `geo`, `timeframe` | string | Có | Cấu hình truy vấn đã chốt |
| `date` | date | Có | Ngày/điểm thời gian trả về |
| `interest_score` | integer/null | Có nếu nguồn trả về | Chỉ số tương đối 0–100 |
| `search_type` | string/null | Nên có | Web, YouTube... |
| `source_url` | string | Có | Mô tả truy vấn có thể tái tạo |
| `retrieved_at` | datetime | Có | Thời điểm lấy |

Bộ từ khóa, địa lý, loại tìm kiếm và timeframe phải chốt trước khi thu thập lịch sử (mục 15). Không so sánh trực tiếp các lần truy vấn chuẩn hóa độc lập nếu chưa có cách nối thang đo.

### 6.5 Gọi vốn và sự kiện

| Trường | Kiểu | Bắt buộc | Ý nghĩa |
| --- | --- | --- | --- |
| `event_id` | string | Có | Khóa sự kiện |
| `company_id`, `event_date` | string/null, date | Có nếu xác định được | Công ty, ngày sự kiện |
| `event_type`, `event_name` | string | Có | Ví dụ funding, partnership, product |
| `amount`, `currency`, `valuation` | decimal/null | Không | Nếu nguồn công bố |
| `source_url` | string | Có | Nguồn cụ thể |
| `retrieved_at` | datetime | Có | Thời điểm thu thập |

Sự kiện dùng cho timeline/bối cảnh. Chỉ trường được quy định rõ trong công thức mới được đưa vào `In`/`Out`.

### 6.6 Giá cổ phiếu

| Trường | Kiểu | Bắt buộc | Ý nghĩa |
| --- | --- | --- | --- |
| `ticker`, `trade_date` | string, date | Có | MSFT/GOOGL, ngày giao dịch |
| `open, high, low, close, adj_close, volume` | decimal/null | Theo nguồn | Giá và khối lượng |
| `source_url`, `retrieved_at` | string, datetime | Có | Truy vết nguồn |

Dữ liệu giá dùng làm bối cảnh/hiển thị, không tự động đưa vào công thức `E`.

### 6.7 Metadata đồng bộ và chất lượng

Mỗi lần chạy thu thập ghi tối thiểu: `run_id, source_name, source_url, started_at, finished_at, sync_status (success/partial/failed), records_read, records_added, records_changed, records_rejected, error_code, error_message, content_hash, retrieved_at, data_status, missing_reason`.

### 6.8 Dữ liệu as-of cho nowcast/forecast

| Trường | Kiểu | Bắt buộc | Ý nghĩa |
| --- | --- | --- | --- |
| `as_of_date` | datetime | Có | Mốc cắt dữ liệu (ngày + giờ) của một lần nowcast/forecast; không dùng bản ghi công bố sau mốc này |
| `available_at` | datetime | Có | Thời điểm dữ liệu thực sự có sẵn cho người dùng |
| `vintage_id` | string | Có | Định danh snapshot dữ liệu gốc dùng cho lần chạy |
| `forecast_origin` | string (`YYYY-QN`) | Có | Quý xuất phát của dự báo |
| `target_period` | string (`YYYY-QN`) | Có | Quý được nowcast/forecast |
| `horizon` | integer | Có | `0` = nowcast, `1` = forecast; baseline không hỗ trợ `> 1` |
| `model_id`, `model_version` | string | Có | Model và phiên bản đã dùng |
| `feature_set_version` | string | Có | Phiên bản feature set và quy tắc chuẩn hóa |

`available_at` khác `retrieved_at`: `retrieved_at` là lúc ĐV-ĐR lấy dữ liệu, còn `available_at` là lúc dữ liệu được công bố/trở nên khả dụng. Backtest phải dùng `available_at`, không dùng `retrieved_at`, để tránh nhìn trước tương lai.

---

## 7. Quy tắc tính toán

### 7.1 Product Score

```text
Product Score = 3 × count(A) + 2 × count(B) + 1 × count(C)
```

A/B/C là các nhóm sản phẩm định nghĩa trong rubric (mục 15). Rubric phải lưu cùng phiên bản để tái tạo kết quả.

### 7.2 Tổng hợp theo quý và MA4Q

* Gộp sản phẩm theo quý dựa trên `announcement_date`.
* Gộp Google Trends theo quý bằng quy tắc đã thống nhất (ví dụ trung bình các điểm hợp lệ trong quý).
* MA4Q là trung bình của bốn quý theo quy tắc đã định; mặc định yêu cầu đủ bốn quý, không tính MA ngắn hơn, để tránh thay đổi ý nghĩa chỉ số.
* Không tạo dữ liệu giả để lấp quý trống.

### 7.3 Z-score

```text
z(x) = (x - mean(x)) / std(x)
```

Phải ghi rõ tập dữ liệu dùng để tính mean/std, cách xử lý `std = 0`, số quý tối thiểu và cách cập nhật khi có quý mới. Nếu dùng toàn bộ lịch sử để chuẩn hóa, dashboard phải nói rõ đây là chuẩn hóa hồi cứu. Với nowcast/forecast, không được dùng toàn bộ lịch sử; mean/std phải tính đến `as_of_date` (FCST-02, FCST-03).

`z16Q` là biến thể z-score dùng cửa sổ 16 quý gần nhất; chỉ tính khi đủ 16 quý, nếu không ghi `status = insufficient_window` và không dùng cho `E`/forecast. Với dữ liệu hiện tại, `z16Q` có 7 cửa sổ đủ/công ty (14 pooled) từ 2024-Q4; 15 quý đầu bị flag.

### 7.4 In, Out và E

```text
Out = w_product × z(Product MA4Q) + w_trends × z(Trends MA4Q)
In  = z(R&D theo quý)
E   = Out - In
```

* Trọng số mặc định: `w_product = 0.6`, `w_trends = 0.4`. Kịch bản độ nhạy: `0.5/0.5` và `0.7/0.3`.
* `In` dùng cùng công thức cho cả Microsoft và Alphabet (Quyết định 2, mục 0), vì cả hai đều công bố R&D trên SEC (Tier S).
* CapEx intensity (`CapEx / Revenue`) có thể dùng làm biến đối chiếu bổ sung cho `In` ở mức độ nhạy tùy chọn (Could, không bắt buộc cho baseline), không thay thế R&D trong công thức mặc định.

Không so sánh `E` giữa hai công ty như xếp hạng hiệu suất tuyệt đối nếu chưa kiểm tra độ nhạy theo trọng số. Không diễn giải `E > 0` thành "đầu tư sinh lời"; chỉ diễn giải là chỉ báo đầu ra chuẩn hóa cao hơn đầu vào chuẩn hóa trong phạm vi định nghĩa của mô hình.

### 7.5 Giá trị thiếu và ngoại lệ

* Giữ `NULL` và ghi `missing_reason`; không thay bằng 0 mặc định.
* Không tính `E` khi `In` hoặc `Out` không đủ dữ liệu.
* Nếu `std = 0`, z-score không xác định; ghi trạng thái phù hợp.
* Ghi log mọi loại bỏ dữ liệu, chuyển đổi đơn vị và chuyển đổi kỳ báo cáo.

### 7.6 Nowcast, forecast và alert

**FCST-01 — Horizon.** Hệ thống hỗ trợ tối đa hai horizon: `h = 0` là nowcast `E` (hoặc các thành phần rồi suy ra `E`) của quý hiện tại trước khi 10-Q được nộp; `h = 1` là forecast `E`/`Out` (hoặc các thành phần) cho quý kế tiếp. Baseline không hỗ trợ `h > 1`.

**FCST-02 — Point-in-time.** Mọi feature và tham số chuẩn hóa dùng để tạo dự báo tại `as_of_date` chỉ được lấy từ dữ liệu có `available_at <= as_of_date`. Trong training/backtest, mỗi mẫu phải mô phỏng đúng thời điểm: feature chỉ dùng dữ liệu có sẵn tại `forecast_origin`, còn target là giá trị thực tế của kỳ target (chỉ dùng để học/đánh giá, không dùng làm feature). Filing, giá, trends hoặc sự kiện công bố sau `as_of_date` không được đưa vào feature. Vi phạm là lỗi chặn, không phải cảnh báo.

**FCST-03 — Target.** Target mặc định là các thành phần `R&D`, `Product MA4Q`, `Trends MA4Q`; từ đó suy ra `E` bằng công thức mục 7.4. Có thể chọn target `E` trực tiếp như một biến thể, nhưng phải ghi trong `config_version`. Nếu `E` dùng z16Q, số quan sát hiệu dụng chỉ còn 14 pooled (7/công ty); phải báo cáo rõ. Mọi tham số chuẩn hóa chỉ dùng dữ liệu đến `as_of_date`; không forecast trực tiếp z-score nếu cửa sổ chuẩn hóa chứa dữ liệu tương lai.

**FCST-04 — Feature set.** Baseline dùng tối đa 10 biến sau khi chọn: lag 1–2 của `E`/`Out`/`In`; `rd_intensity` (lag); `capex_intensity` (lag); `Product Score`/`MA4Q` (lag); `Trends MA4Q` (lag); số sự kiện theo nhóm A/B/C; market context đến `as_of_date` (tùy chọn); company dummy; seasonality. Lag 1–2 chỉ là feature dự báo ngắn hạn, không phải mô hình lag analysis 0–4 quý đã loại ở Quyết định 3. Feature set phải được version hóa trong `feature_set_version`.

**FCST-05 — Model.** Baseline bắt buộc: naive/AR(1). Model chính: Ridge, Elastic Net hoặc Bayesian Ridge. Lý do: `N` nhỏ, feature ít và có tương quan, cần regularization và diễn giải; mô hình tuyến tính có hệ số ổn định hơn DL. XGBoost cây nông chỉ là benchmark tùy chọn. **Không dùng Deep Learning** (LSTM/Transformer/DeepAR) trong baseline vì `N` tối đa 44 pooled (22 quý/công ty) cho target thành phần, và chỉ 14 pooled nếu target `E` trực tiếp dùng z16Q; chỉ xem xét khi dữ liệu mở rộng và có quyết định mới. Baseline ưu tiên pooled model có company dummy; nếu chạy per-company phải báo cáo riêng và nêu rõ `N = 22` (hoặc `N = 7` nếu target `E` trực tiếp).

**FCST-06 — Validation.** Phải dùng rolling-origin backtest, không random split. Mỗi fold huấn luyện trên dữ liệu đến `t`, test trên kỳ target (`t` cho nowcast, `t + 1` cho forecast), rồi cuộn tiếp. Model selection/tuning phải nằm trong train; test chỉ dùng để báo cáo. Nếu dùng cùng rolling-origin cho cả selection và báo cáo, phải ghi rõ và không overclaim. Báo cáo tối thiểu MAE, RMSE, directional accuracy và so sánh với naive/AR(1), riêng từng công ty và pooled. Số fold tối thiểu là 6 nếu dữ liệu cho phép; nếu target `E` trực tiếp, báo cáo số fold thực tế và không overclaim.

**FCST-07 — Uncertainty.** Mọi kết quả phải có khoảng 80% và 95% (conformal prediction hoặc Bayesian interval). Nếu target là thành phần, interval của `E` phải được suy ra (Monte Carlo hoặc conformal trên `E`), không chỉ lấy interval của một thành phần. Báo cáo empirical coverage trên backtest. Không hiển thị point forecast mà không có interval.

**FCST-08 — Quality gate.** Nếu model không beat naive/AR(1) trên pooled MAE hoặc RMSE của target chính (và của `E` suy ra nếu target là thành phần) ở backtest, không được gắn nhãn "forecast" trên dashboard; chỉ hiển thị "experimental/insufficient evidence" hoặc ẩn. Kết quả vẫn phải được lưu để audit. Không đặt target MAE cứng trước khi có backtest; kết quả thực tế quyết định việc hiển thị.

**FCST-09 — Alert.** Alert rule tối thiểu: (a) interval 80% của `E` forecast cắt 0; (b) point forecast `E` dưới `alert_threshold` trong config; (c) nowcast lệch khỏi giá trị `E` đã công bố gần nhất quá ngưỡng. Mỗi alert ghi `alert_id`, `company_id`, `target_period`, `horizon`, `rule_id`, `severity`, `message`, `as_of_date`, `model_run_id`; severity dùng `INFO`, `WARN`, `CRITICAL`, ngưỡng cụ thể ở config. Alert chỉ được đánh giá trên forecast result có trạng thái hợp lệ và đã qua quality gate; không alert trên fallback/insufficient data. Alert nhị phân (b, c) được coi là đúng nếu `E` thực tế của kỳ target vi phạm cùng điều kiện; rule (a) báo cáo tỷ lệ interval chứa giá trị thực thay vì precision. Báo cáo precision/false-positive từ backtest cho các rule nhị phân.

**FCST-10 — Driver attribution.** Dashboard phải hiển thị top 3 yếu tố đóng góp vào nowcast/forecast (hệ số chuẩn hóa hoặc SHAP), gắn nhãn "yếu tố đóng góp", không phải quan hệ nhân quả. Nếu target là thành phần, top 3 phải quy về đóng góp cho `E` (qua trọng số 0.6/0.4 và z-score), không chỉ đóng góp cho một thành phần.

**FCST-11 — Model card và reproducibility.** Mỗi model version phải có model card: mục tiêu, feature, dữ liệu huấn luyện, `as_of` policy, hyperparameters (gồm `random_state`), metric backtest, interval method, giới hạn và artifact hash. Cùng snapshot + model version + config (gồm `random_state`) phải cho cùng kết quả.

**FCST-12 — Fallback và labeling.** Nếu thiếu dữ liệu hoặc model lỗi, fallback naive/AR(1) hoặc hiển thị "insufficient data"; không bịa số. Fallback naive chỉ để giữ pipeline chạy; không được gắn nhãn "forecast" nếu chưa qua FCST-08. Mọi output phải gắn nhãn "experimental", `as_of_date`, model version, interval và câu "không phải khuyến nghị đầu tư".

---

## 8. Data model và lưu trữ

### 8.1 Các bảng/nhóm dữ liệu logic

1. `companies` — danh mục công ty và cấu hình phương pháp đầu vào.
2. `source_registry` — tên nguồn, loại nguồn, URL gốc, tier, quy tắc truy cập.
3. `raw_records` — dữ liệu gốc, payload/file reference, hash, thời gian thu thập.
4. `financial_quarterly` — R&D, revenue, CapEx, kỳ tài chính, filing metadata.
5. `ai_products` — sản phẩm/công bố AI và kết quả phân loại A/B/C.
6. `google_trends` — interest score theo từ khóa/thời gian/địa lý.
7. `events` — gọi vốn, hợp tác, mốc liên quan.
8. `market_daily` — giá cổ phiếu theo ngày.
9. `features_quarterly` — Product Score, Trends tổng hợp, MA4Q, z-score.
10. `analysis_results` — `In`, `Out`, `E`, kịch bản trọng số, phiên bản công thức.
11. `sync_log` — nhật ký từng lần chạy.
12. `data_quality_log` — lỗi validation, dữ liệu thiếu, quyết định xử lý.
13. `feature_snapshots` — feature values tại một `as_of_date`, phục vụ nowcast/backtest tái lập.
14. `model_registry` — model_id, loại model, version, feature set, hyperparameters, training window, metric, artifact hash.
15. `forecast_runs` — một lần chạy nowcast/forecast: `run_id`, `model_id`, `as_of_date`, `forecast_origin`, `horizon`, `feature_snapshot_id`, `config_version`, `status`.
16. `forecast_results` — point forecast, interval 80%/95%, `target_period`, `company_id`, `run_id`, `status`, `reason`.
17. `alert_log` — `alert_id`, `rule_id`, `severity`, `company_id`, `target_period`, `triggered_at`, `forecast_result_id`, `status`.

> **Lược bỏ so với bản trước:** bảng `ai_spending_estimates` (ước tính chi tiêu AI độ tin cậy thấp, dành cho công ty tư nhân) không nằm trong baseline này, vì cả hai công ty trong phạm vi đều niêm yết và có R&D từ SEC (Quyết định 2, mục 0). Schema có thể khôi phục nếu phạm vi mở rộng sang công ty tư nhân trong tương lai.

### 8.2 Khóa và tính toàn vẹn

* Mỗi bảng có khóa chính ổn định.
* Dữ liệu sự kiện/sản phẩm cần khóa chống trùng dựa trên ID nguồn hoặc quy tắc khử trùng tài liệu hóa.
* Bản ghi gốc đã thu thập không bị âm thầm ghi đè; thay đổi lưu thành phiên bản hoặc bản ghi mới (append-only).
* Mỗi kết quả phân tích tham chiếu phiên bản dữ liệu đầu vào, thời điểm chạy và phiên bản công thức.
* `forecast_results` unique theo `(run_id, company_id, target_period, horizon)`.
* `forecast_runs` tham chiếu `model_id` và `feature_snapshot_id`; `alert_log` tham chiếu `forecast_result_id`.
* Model artifact phải có hash và không bị ghi đè; version mới tạo bản ghi mới trong `model_registry`.

### 8.3 Từ điển đặc trưng cốt lõi

| Đặc trưng | Định nghĩa | Nguồn | Tier | Derived |
| --- | --- | --- | --- | --- |
| Revenue | Doanh thu quý đã báo cáo | SEC | S | Không |
| R&D | Chi phí R&D đã báo cáo | SEC | S | Không |
| Product Score | `3×A + 2×B + 1×C` theo rubric | Derived | A (kế thừa) | Có |
| Trends MA4Q | Trung bình động 4 quý của interest score | Google Trends | B | Có |
| `In` | `z(R&D theo quý)` | SEC | S (kế thừa) | Có |
| `Out` | Tổ hợp trọng số Product MA4Q và Trends MA4Q | Derived | — | Có |
| `E` | `Out − In` | Derived | — | Có |
| `E_nowcast` | Nowcast `E` của quý hiện tại (`h = 0`) | Derived | — | Có |
| `E_forecast` | Forecast `E` của quý kế tiếp (`h = 1`) | Derived | — | Có |
| `forecast_interval` | Lower/upper 80% và 95% của forecast | Derived | — | Có |
| `alert_flag` | Có alert đang active cho công ty/kỳ | Derived | — | Có |
| Stock Price | Giá đóng cửa điều chỉnh | Yahoo Finance | B | Không |

---

## 9. Pipeline thu thập và xử lý

1. **Collect** — chạy theo lịch, lấy dữ liệu từ nguồn đã cấu hình.
2. **Archive** — lưu raw snapshot/CSV append-only, URL và thời gian lấy.
3. **Validate** — kiểm tra schema, kiểu dữ liệu, đơn vị, kỳ, trùng lặp, trường bắt buộc.
4. **Normalize** — chuẩn hóa đơn vị và kỳ báo cáo; tách số quý khỏi số lũy kế khi có căn cứ.
5. **Transform** — phân loại sản phẩm, tổng hợp theo quý, tính MA4Q và z-score.
6. **Compute** — tính `In`, `Out`, `E` và các kịch bản trọng số.
7. **Forecast/Nowcast** — tạo feature snapshot as-of, chạy model, xuất point forecast + interval, ghi `forecast_runs`/`forecast_results`.
8. **Alert** — đánh giá alert rule, ghi `alert_log`.
9. **Publish** — xuất JSON/SQLite hoặc artifact để dashboard đọc.
10. **Monitor** — cập nhật manifest, trạng thái đồng bộ và lỗi.

**PIPE-01.** Lịch đề xuất (có thể cấu hình): dữ liệu thị trường sau phiên giao dịch (nhịp nhanh, vài giờ/lần); SEC/IR, sản phẩm AI và sự kiện theo lịch hằng ngày (nhịp chậm). Nowcast cập nhật sau mỗi lần crawl dữ liệu tần suất cao; forecast chạy khi có đủ dữ liệu quý hoặc theo lịch ngày. Đây là lịch vận hành đề xuất, không phải cam kết SLA của nhà cung cấp.

**PIPE-02.** Dashboard không crawl trực tiếp nguồn ngoài khi người dùng mở trang. Dashboard đọc dữ liệu đã xử lý và trạng thái đồng bộ gần nhất.

**PIPE-03.** Mọi bước forecast/nowcast phải đọc từ `feature_snapshots` as-of; không đọc trực tiếp bảng raw mới nhất. Backtest và inference phải dùng cùng logic point-in-time.

**PIPE-04.** Forecast là feature flag: nếu model lỗi hoặc thiếu dữ liệu, fallback naive/AR(1) hoặc ẩn kết quả; không chặn pipeline `E` chính.

**PIPE-05.** Training/backtest chạy offline, không chạy trong cron production; cron production chỉ chạy inference và ghi kết quả. Model mới phải qua quality gate trước khi promote.

---

## 10. Yêu cầu dashboard

### 10.1 Chế độ xem

| Mã | Trang | Nội dung |
| --- | --- | --- |
| DSH-01 | E Score theo quý | Đồ thị `E` theo thời gian, chú giải, tooltip |
| DSH-02 | Input vs Output | `In` và `Out` trên biểu đồ riêng hoặc chung, nhãn giải thích |
| DSH-03 | Timeline sự kiện | Mốc gọi vốn, hợp tác, công bố sản phẩm, liên kết nguồn |
| DSH-04 | Weight Sensitivity | So sánh kết quả của bộ trọng số 0.6/0.4, 0.5/0.5, 0.7/0.3 |
| DSH-05 | Data Status & Evidence | Kỳ dữ liệu mới nhất, thời gian đồng bộ, trạng thái, dữ liệu thiếu, liên kết nguồn |
| DSH-06 | Market Context | Giá cổ phiếu theo ngày của MSFT và GOOGL, nếu giữ trong phạm vi phát hành (Should) |
| DSH-07 | lớp dự báo ĐV-ĐR — Forecast & Alerts | Nowcast/forecast `E` với interval 80%/95%, alert badge, top 3 driver attribution, `as_of_date`, model version, link model card |

### 10.2 Quy tắc hiển thị

* Hiển thị đơn vị, kỳ, công ty và định nghĩa chỉ số.
* Phân biệt rõ dữ liệu công bố, dữ liệu derived.
* Có liên kết `source_url` cho dữ liệu quan trọng.
* Khi dữ liệu thiếu, hiển thị "Không đủ dữ liệu"; không vẽ số 0 gây hiểu nhầm.
* Gắn cảnh báo rằng `E` không phải ROI và không chứng minh nhân quả.
* Dashboard không tự tính số liệu tài chính từ số nhập tay (chỉ đọc `features_quarterly`/`analysis_results`/`forecast_results` đã tính sẵn).
* DSH-07 phải gắn nhãn "experimental", hiển thị `as_of_date`, model version, interval và câu "không phải khuyến nghị đầu tư".
* Không hiển thị point forecast mà không có interval; nếu quality gate không đạt, hiển thị "insufficient evidence" thay vì số dự báo.
* Driver attribution phải ghi "yếu tố đóng góp", không diễn giải là nhân quả.

---

## 11. Yêu cầu phi chức năng

| Mã | Yêu cầu | Xác minh |
| --- | --- | --- |
| NFR-01 | Tái lập: cùng dữ liệu đầu vào và cùng phiên bản công thức cho cùng kết quả | Chạy lại pipeline, so sánh `analysis_results` |
| NFR-02 | Truy vết: mọi con số chính trên dashboard lần được đến `source_id`/`source_url` | Kiểm tra `source_id → source_url` |
| NFR-03 | Quản lý phiên bản cấu hình: trọng số, ngưỡng, công thức có `version`, lưu cùng kết quả | Kiểm tra schema |
| NFR-04 | Khả năng phục hồi: lỗi một nguồn không làm mất dữ liệu đã thu thập từ nguồn khác | Kiểm thử lỗi giả lập |
| NFR-05 | Hiệu năng: tải dashboard không quá 3 giây trong môi trường demo | Đo kiểm khi nghiệm thu |
| NFR-06 | Bảo mật cấu hình: token/API key nằm trong secrets/environment, không commit vào repo | Rà soát repo |
| NFR-07 | Tuân thủ nguồn: tôn trọng điều khoản, `robots.txt`, giới hạn truy cập, yêu cầu User-Agent | Rà soát `source_registry` |
| NFR-08 | Khả năng bảo trì: tách module collection, validation, transformation, computation, forecast, display | Rà soát kiến trúc |
| NFR-09 | Point-in-time: không dùng dữ liệu công bố sau `as_of_date` trong train/backtest/inference | Replay snapshot + kiểm tra timestamp |
| NFR-10 | Tái lập forecast: cùng snapshot + model version + config cho cùng kết quả | Chạy lại, so sánh hash/kết quả |
| NFR-11 | Minh bạch forecast: có model card, feature list, metric backtest, interval method | Review model card |
| NFR-12 | Suy giảm có kiểm soát: model lỗi/thiếu dữ liệu thì fallback naive hoặc ẩn, không chặn dashboard `E` | Kiểm thử lỗi giả lập |
| NFR-13 | Hiệu năng forecast: inference cho 2 công ty dưới 30 giây trong môi trường demo | Đo kiểm |
| NFR-14 | Guardrail small-N: tối đa 10 biến baseline, bắt buộc so sánh naive/AR(1), không dùng DL | Review config + backtest report |
| NFR-15 | Audit alert: mọi alert truy vết được rule, forecast result, model run và `as_of_date` | Kiểm tra `alert_log` |

---

## 12. Công nghệ dự kiến

* **Collection/Scheduling:** Python, GitHub Actions.
* **Nguồn tài chính:** SEC EDGAR/XBRL, trang IR chính thức; `yfinance` cho giá cổ phiếu.
* **Google Trends:** `pytrends`, có xử lý lỗi và giới hạn nguồn.
* **Processing:** Python, pandas, NumPy.
* **Modeling:** scikit-learn (Ridge, ElasticNet, BayesianRidge); `mapie` hoặc split-conformal tự triển khai cho interval; statsmodels nếu cần; `joblib` cho model artifact. Không dùng PyTorch/TensorFlow trong baseline.
* **Forecast storage:** `feature_snapshots`, `model_registry`, `forecast_runs`, `forecast_results`, `alert_log` dạng CSV/JSON/SQLite.
* **Storage:** CSV append-only và SQLite/JSON cho dữ liệu đã xử lý.
* **Dashboard:** React; host tĩnh (GitHub Pages).
* **Testing:** kiểm thử đơn vị cho chuẩn hóa, gộp quý, Product Score, MA4Q, z-score, `In`, `Out`, `E`, xử lý dữ liệu thiếu; kiểm thử point-in-time, rolling-origin backtest, interval coverage, alert rule và fallback.

Tên thư viện có thể thay đổi khi triển khai, nhưng phải bảo toàn hành vi đã đặc tả.

---

## 13. Xác minh và chấp nhận

### 13.1 Ma trận xác minh

| Yêu cầu | Mã | Phương pháp xác minh |
| --- | --- | --- |
| Dữ liệu tài chính có nguồn | SRC-03 | Kiểm toán source registry |
| Dữ liệu SEC là chuẩn khi xung đột | SRC-04 | Đối chiếu chéo nguồn |
| Căn chỉnh quý lịch đúng | DAT-01 | Kiểm tra `period_end_date` |
| Product Score đúng rubric | §7.1 | Tính tay, so sánh |
| MA4Q, z-score đúng công thức | §7.2, §7.3 | Kiểm thử công thức, trường hợp `std=0` |
| `In`, `Out`, `E` đúng công thức | §7.4 | Tính tay một số giá trị, so sánh |
| Độ nhạy theo trọng số | §7.4 | Chạy ba bộ trọng số, so sánh |
| Dashboard đọc đúng dữ liệu đã xử lý | DSH-01…07 | Đối chiếu dashboard với `analysis_results`/`forecast_results` |
| Truy vết nguồn | NFR-02 | Kiểm tra `source_id → source_url` |
| Nowcast/forecast chỉ dùng dữ liệu as-of | FCST-02, PIPE-03 | Replay snapshot; kiểm tra không có feature nào có `available_at > as_of_date` |
| Forecast beat baseline | FCST-06, FCST-08 | Rolling-origin backtest; MAE/RMSE/directional accuracy so với naive/AR(1) |
| Interval coverage | FCST-07 | Đo empirical coverage 80%/95% trên backtest |
| Alert rule | FCST-09 | Scenario test + `alert_log`; báo cáo precision |
| Model card và tái lập | FCST-11, NFR-10 | Review model card; chạy lại cùng snapshot/config |
| Dashboard forecast | DSH-07 | So sánh với `forecast_results`; kiểm tra nhãn experimental/interval |

### 13.2 Tiêu chí chấp nhận

**Dữ liệu**
- [ ] Thu thập 22 quý/công ty (44 quan sát) từ 2021-Q1 đến 2026-Q2, với 2021 là warm-up cho MA4Q.
- [ ] Có nguồn SEC cho báo cáo tài chính; có nguồn IR cho chỉ số vận hành đặc thù.
- [ ] Có dữ liệu thị trường cho giai đoạn phân tích (MSFT, GOOGL).
- [ ] Mọi quan sát có `source_id`.
- [ ] Dữ liệu hai công ty được căn chỉnh theo quý lịch (DAT-01).
- [ ] Mọi giá trị lấy từ nguồn thật; không có dữ liệu mock hay ước tính không nguồn.

**Tính toán**
- [ ] Đã tính Product Score theo rubric đã chốt (mục 15).
- [ ] Đã tính Trends MA4Q, z-score, xử lý đúng `std = 0` và số kỳ không đủ.
- [ ] Đã tính `In`, `Out`, `E` cho cả hai công ty bằng cùng công thức `In`.
- [ ] Đã kiểm tra ba bộ trọng số độ nhạy.
- [ ] Không tính `E` khi một thành phần bắt buộc không khả dụng.

**Dashboard**
- [ ] Bảy chế độ xem (DSH-01…07) hiển thị đúng kỳ, công ty, đơn vị, giá trị.
- [ ] Tooltip/timeline có thông tin nguồn.
- [ ] Trạng thái đồng bộ phản ánh đúng lần chạy gần nhất.
- [ ] Dữ liệu thiếu không hiển thị sai thành số 0.
- [ ] Có cảnh báo diễn giải `E` đúng (không phải ROI, không chứng minh nhân quả).

**Nowcast/Forecast**
- [ ] Pipeline nowcast/forecast chạy cho cả MSFT và GOOGL với `h = 0` và `h = 1`.
- [ ] Có rolling-origin backtest tối thiểu 6 fold (hoặc báo cáo số fold thực tế nếu target `E` trực tiếp); báo cáo MAE, RMSE, directional accuracy của target và `E` suy ra (nếu target là thành phần) so với naive/AR(1), riêng từng công ty và pooled.
- [ ] Kết quả có interval 80%/95%; báo cáo empirical coverage.
- [ ] Không có look-ahead: mọi feature có `available_at <= as_of_date`.
- [ ] Quality gate FCST-08 được áp dụng; nếu không đạt, dashboard ghi "insufficient evidence" hoặc ẩn.
- [ ] `forecast_results` có `run_id`, `model_id`, `as_of_date`, `target_period`, interval và trạng thái.
- [ ] `alert_log` ghi đủ rule, severity, `forecast_result_id`; có báo cáo precision/false positive.
- [ ] Có model card và artifact hash; chạy lại cùng snapshot/config cho cùng kết quả.
- [ ] DSH-07 hiển thị nhãn "experimental", interval, `as_of_date`, model version và "không phải khuyến nghị đầu tư".

### 13.3 Định nghĩa hoàn thành (Definition of Done)

ĐV-ĐR hoàn thành khi một reviewer có thể chọn bất kỳ con số chính nào trên dashboard và truy vết:

```text
Dashboard → Analysis Result (E/Out/In) → Feature (Product Score/Trends MA4Q/z-score)
→ Raw Data → Source ID → Source URL → SEC / Công bố chính thức của công ty
```

rồi tự tái lập được kết quả. Khả năng truy vết này là tiêu chí chấp nhận cốt lõi của hệ thống.

Với nowcast/forecast, reviewer phải truy vết được:

```text
DSH-07 → Forecast Result → Forecast Run → Feature Snapshot → Model Registry
→ Raw Data → Source ID → Source URL
```

và kiểm tra được `as_of_date`, model version, interval, metric backtest và model card.

---

## 14. Rủi ro và giới hạn

1. R&D tổng thể không chỉ dành cho AI; đây là proxy (độ tin cậy MEDIUM/LOW theo SRC-06).
2. Google Trends là chỉ số tương đối, chịu ảnh hưởng của từ khóa, địa lý và cách truy vấn.
3. Chuỗi dữ liệu 22 quý/công ty (44 quan sát) từ 2021-Q1 vẫn nhỏ; z16Q chỉ có 7 cửa sổ đủ/công ty (14 pooled) từ 2024-Q4; kết quả nhạy với lựa chọn khoảng thời gian, chuẩn hóa và feature.
4. Hai công ty có kỳ tài chính và mức độ công bố sản phẩm khác nhau.
5. `E` là chỉ số mô tả tương đối, không phải ROI, lợi nhuận hay quan hệ nhân quả.
6. Phạm vi giới hạn ở hai công ty niêm yết; kết luận không khái quát hóa được cho công ty tư nhân hay toàn ngành AI (xem mục 0).
7. Các nguồn web/API có thể thay đổi cấu trúc hoặc giới hạn truy cập; pipeline phải có logging và xử lý lỗi.
8. Với `N = 44` (hoặc 14 pooled nếu target `E` trực tiếp dùng z16Q), model forecast có thể không beat naive/AR(1); khi đó phải công bố trung thực và áp dụng quality gate FCST-08, không thổi phồng kết quả.
9. Target z-score có thể không ổn định khi cửa sổ chuẩn hóa thay đổi; ưu tiên forecast thành phần hoặc dùng tham số chuẩn hóa cố định đến `as_of_date`.
10. Look-ahead là rủi ro nghiêm trọng nhất của nowcast/backtest; phải kiểm tra `available_at`, không dùng `retrieved_at` làm mốc.
11. Alert có thể tạo false positive; phải báo cáo precision và cho phép tắt/ngưỡng cấu hình.
12. Model drift khi dữ liệu mới thay đổi phân phối; phải retrain/version hóa và không tự động promote model mới.
13. Nowcast/forecast là thử nghiệm, không phải khuyến nghị đầu tư; không dùng để giao dịch tự động.
14. Deep Learning không phù hợp ở quy mô hiện tại; nếu mở rộng dữ liệu, phải đánh giá lại bằng backtest trước khi thay model.
15. Product Score/MA4Q phụ thuộc sự kiện công bố; với `h = 1`, model không biết sự kiện tương lai, nên forecast chủ yếu dựa vào momentum/trends và có thể kém chính xác hơn nowcast.

---

## 15. Các quyết định còn cần nhóm xác nhận

Phạm vi công ty và phương pháp `In` (hai vấn đề mở quan trọng nhất của các bản trước) đã được khóa ở mục 0. Các mục dưới đây vẫn cần nhóm xác nhận trước khi triển khai Phase 2.5:

1. **Rubric A/B/C:** định nghĩa chính thức, ví dụ cụ thể, quy tắc khử trùng sản phẩm (preview vs bản chính thức vs bài blog lặp lại).
2. **Google Trends:** bộ từ khóa, địa lý, loại tìm kiếm, cách gộp từ ngày/tuần sang quý.
3. **Z-score:** chuẩn hóa trên toàn bộ lịch sử hay theo cửa sổ trượt; số quý tối thiểu.
4. **MA4Q:** xác nhận yêu cầu đủ bốn quý (mặc định hiện tại), không cho phép cửa sổ ngắn hơn.
5. **CapEx như biến đối chiếu:** có triển khai ở bản đầu tiên hay để sau (hiện đánh dấu Could, không bắt buộc).
6. **DSH-06 (Market Context):** giữ hay bỏ khỏi bản phát hành đầu tiên (hiện đánh dấu Should).
7. **Lịch đồng bộ:** tần suất cuối cùng theo từng nguồn (PIPE-01 chỉ là đề xuất).
8. **Target forecast:** mặc định forecast thành phần `R&D`/`Product MA4Q`/`Trends MA4Q` rồi suy ra `E`; có bổ sung target `E` trực tiếp hay không, và ghi lựa chọn trong `config_version`.
9. **Model family:** chọn Ridge, Elastic Net hay Bayesian Ridge cho baseline; có giữ XGBoost làm benchmark hay không.
10. **Alert threshold/severity:** ngưỡng cụ thể cho từng rule, severity mặc định và cách hiển thị.
11. **DSH-07:** đưa vào bản phát hành đầu tiên hay sau khi backtest đạt quality gate.
12. **Mở rộng tùy chọn:** có làm **B — causal event study** (event study/abnormal return) hoặc **C — LLM event intelligence** (trích xuất sự kiện bằng LLM) sau baseline A hay không; cả hai không thuộc phạm vi bắt buộc.

Cho đến khi các mục trên được chốt, xem chúng là quyết định mở, không tự coi là yêu cầu đã phê duyệt.

---

## Phụ lục A — Ma trận truy vết

| Câu hỏi nghiên cứu | Yêu cầu liên quan | Bảng dữ liệu | Trang dashboard |
| --- | --- | --- | --- |
| RQ-01 Đầu vào | DAT §6.2, CALC §7.4 (`In`) | `financial_quarterly`, `features_quarterly` | DSH-02 |
| RQ-02 Đầu ra | DAT §6.3, §6.4, CALC §7.1–7.2 | `ai_products`, `google_trends`, `features_quarterly` | DSH-02 |
| RQ-03 Điểm E | CALC §7.4 | `analysis_results` | DSH-01 |
| RQ-04 Độ nhạy trọng số | CALC §7.4 | `analysis_results` | DSH-04 |
| RQ-05 Nowcast | FCST §7.6 (FCST-01…12), PIPE-03 | `feature_snapshots`, `forecast_runs`, `forecast_results` | DSH-07 |
| RQ-06 Forecast | FCST §7.6 (FCST-01…12), PIPE-05 | `model_registry`, `forecast_runs`, `forecast_results` | DSH-07 |
| RQ-07 Alert | FCST-09, NFR-15 | `alert_log`, `forecast_results` | DSH-07 |
| (Bối cảnh sự kiện) | DAT §6.5 | `events` | DSH-03 |
| (Bối cảnh thị trường) | DAT §6.6, SRC-08 | `market_daily` | DSH-06 |
| (Truy vết) | SRC-03, NFR-02 | `source_registry`, `data_quality_log` | DSH-05 |

---

## 16. Ghi chú triển khai (implementation notes)

Phần này ghi lại các quyết định đã thực thi, để SPEC không mô tả sai code hiện có.

| # | Điểm | Thực thi | Lý do / tham chiếu |
|---|---|---|---|
| 1 | `z16Q` | Cửa sổ **16 quý gần nhất** (trailing), tính riêng từng công ty; chỉ phát giá trị khi đủ 16 quý, nếu không `status=insufficient_window` + `NULL`. Với dữ liệu 2021Q1→2026Q2: 7 quý/công ty có `E`. | §7.3 yêu cầu đủ 16 quý và nêu 7 cửa sổ/công ty; cửa sổ trượt cũng bảo đảm point-in-time. |
| 2 | Forecast target | `E` trực tiếp, pooled có company dummy; ghi trong `config/analysis.yaml` (`target: E`) và model card. | FCST-03 cho phép biến thể nếu ghi trong `config_version`; N=14 pooled không đủ chia cho 3 target thành phần. |
| 3 | Horizon | `h=0` = quý hiện tại chưa có 10-Q (origin+1); `h=1` = quý kế tiếp (origin+2). | FCST-01; `forecast_origin`/`target_period` ghi trong artifact. |
| 4 | Model | Ridge closed-form trong NumPy (không thêm scikit-learn); naive và AR(1) làm baseline bắt buộc. | FCST-05 cấm Deep Learning; N nhỏ, cần determinism và ít dependency. ADR-0007. |
| 5 | Intervals | Split-conformal trên calibration block theo thời gian; fallback normal nếu <3 residual và **ghi rõ** `normal_fallback`. | FCST-07; không nâng cấp ngầm thành conformal. |
| 6 | Quality gate | Fail-closed: nếu không beat naive trên MAE **và** RMSE thì `status=insufficient_evidence`, alert `suppressed`, UI chỉ hiển thị khối tham khảo experimental. | FCST-08. Trên dữ liệu hiện tại gate **không đạt** — kết quả được báo cáo trung thực. |
| 7 | Dashboard | Ứng dụng tĩnh `web/` (HTML + ES modules + SVG), không build step; đọc payload JSON đã publish và kiểm tra SHA-256 trước khi render. | Không có frontend trong checkout; tránh thêm toolchain Node cho 7 view chỉ đọc. ADR-0007. |
| 8 | Publish | `web/data/runs/<run_id>.json` bất biến + `manifest.json` thay thế atomic; giữ 5 phiên bản gần nhất. | PIPE-02; UI không bao giờ đọc dữ liệu dở dang. |
| 9 | `available_at` | Ngày filing **đầu tiên** (10-Q/10-K) báo cáo kỳ đó, lấy từ snapshot SEC; nếu thiếu thì `period_end + 45 ngày` và ghi `available_at_basis=period_end_plus_45d`. Restatement không được mô hình hoá. | FCST-02, NFR-09. |
| 10 | Automation | GitHub Actions theo lịch + `concurrency` + lock; mỗi crawler chạy subprocess độc lập, retry backoff; lỗi 1 nguồn → `partial`. | PIPE-01, NFR-04. Không có SLA 24×7. |
