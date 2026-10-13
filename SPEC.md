# AICOR — Hiệu quả đầu tư AI và tác động kinh doanh của Microsoft và Alphabet

## Đặc tả yêu cầu hệ thống (System Requirements Specification — SRS)

| Thuộc tính | Giá trị |
| --- | --- |
| Mã tài liệu | AICOR-SRS |
| Trạng thái | Nghiên cứu / Đặc tả triển khai |
| Hệ thống | AICOR — AI Investment & Corporate Outcome Research |
| Đối tượng so sánh | Microsoft Corporation (MSFT) và Alphabet Inc. (GOOGL / GOOG) |
| Đơn vị phân tích chính | Công ty × Quý (xem DAT-01 về căn chỉnh quý lịch) |
| Sàn giao dịch | NASDAQ |
| Khoảng dữ liệu chính | 16–20 quý, tùy mức sẵn có của dữ liệu |

### Quy ước dịch

Tên trường dữ liệu, tên bảng, mã yêu cầu, tên tier, giá trị trạng thái (`ROBUST`, `SENSITIVE`, `NULL`…) và các thuật ngữ kỹ thuật chuẩn (CapEx, FCF, CAR, lag, regime…) được giữ nguyên tiếng Anh để khớp với mã nguồn và cơ sở dữ liệu.

---

# 1. Giới thiệu

## 1.1 Mục đích

AICOR là hệ thống nghiên cứu và phân tích nhằm đánh giá mức độ hiệu quả mà các công ty công nghệ niêm yết lớn chuyển hóa nguồn lực và vốn đầu tư liên quan đến AI thành kết quả kinh doanh đo lường được.

Hệ thống so sánh hai công ty:

* Microsoft
* Alphabet

Hệ thống **không** cố ước tính một con số kế toán ẩn gọi là "AI Investment".

Thay vào đó, hệ thống tách bạch bốn nhóm dữ liệu:

1. dữ liệu tài chính đã báo cáo;
2. chỉ số liên quan đến AI mà công ty công bố rõ ràng;
3. đặc trưng tài chính được suy ra (derived);
4. biến đại diện cho đầu tư AI (AI investment proxy).

Sự tách bạch này là bắt buộc, vì báo cáo tài chính của cả hai công ty đều không có một dòng kế toán chuẩn hóa theo quý mang tên `AI Investment`.

## 1.2 Cơ sở xây dựng đặc tả

Đặc tả này theo cấu trúc kỹ thuật yêu cầu (requirements engineering) chịu ảnh hưởng từ Viện Kỹ thuật Phần mềm của Carnegie Mellon (CMU/SEI).

Theo mô tả của CMU/SEI, định nghĩa yêu cầu gồm:

* xác định yêu cầu (identification);
* phân tích yêu cầu (analysis);
* biểu diễn yêu cầu (representation);
* truyền đạt yêu cầu (communication);
* tiêu chí và quy trình chấp nhận (acceptance criteria and procedures).

CMU/SEI cũng định nghĩa đặc tả là một kế hoạch hoặc tiêu chuẩn mô tả cách xây dựng sản phẩm hoặc cách thực hiện quy trình.

Vì vậy, AICOR được xem là một **hệ thống nghiên cứu**, không chỉ là một dashboard. Các URL tham chiếu nằm ở mục 1.5.

## 1.3 Phạm vi

### 1.3.1 Trong phạm vi

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

Báo cáo 10-Q của Microsoft trên SEC xác nhận MSFT niêm yết trên Nasdaq và cung cấp dữ liệu tài chính XBRL/iXBRL.

Hồ sơ SEC của Alphabet xác định Alphabet Inc. và cung cấp khung báo cáo tài chính hằng quý.

### 1.3.2 Ngoài phạm vi

Các nội dung sau bị loại khỏi vai trò bằng chứng tài chính chính:

* ước tính tài chính của công ty chưa niêm yết;
* ước tính của giới phân tích được trình bày như kết quả thực tế;
* bài báo, tin tức dùng thay cho báo cáo tài chính;
* tuyên bố trên mạng xã hội chưa được kiểm chứng;
* các con số "chi tiêu cho AI" chung chung, không có nguồn;
* so sánh công ty phần cứng để thay thế cho phân tích phần mềm/đám mây;
* dữ liệu giả (mock) hoặc bất kỳ biến nào không có nguồn thật lấy về được, gồm đầu tư AI trực tiếp, Copilot, Gemini.

## 1.4 Định nghĩa, thuật ngữ và viết tắt **[BỔ SUNG]**

| Thuật ngữ | Ý nghĩa trong tài liệu này |
| --- | --- |
| AI Investment Proxy | Biến đại diện, được gán nhãn rõ, dùng khi công ty không công bố trực tiếp khoản đầu tư AI (ví dụ R&D, CapEx). |
| CapEx | Chi tiêu vốn (capital expenditure), giữ theo định nghĩa của nguồn (xem FR-03). |
| CFO | Dòng tiền từ hoạt động kinh doanh (cash flow from operations). |
| FCF | Dòng tiền tự do, `CFO − CapEx` (xem FR-05). |
| CAR | Abnormal return tích lũy (cumulative abnormal return) trong cửa sổ sự kiện. |
| YoY / QoQ | Tăng trưởng so với cùng kỳ năm trước / so với quý liền trước. |
| Lag | Độ trễ (số quý) giữa đầu vào và đầu ra. |
| Regime | Trạng thái vận hành của một công ty tại một thời điểm, xác định từ đầu tư, đầu ra và hiệu quả (mục 4.10). |
| Tier S / A / B / R | Bậc tin cậy của nguồn dữ liệu (mục 3.1). |
| Reported / Derived / Proxy | Ba trạng thái của một chỉ số: được báo cáo trực tiếp / được tính từ chỉ số khác / là biến đại diện gián tiếp. |
| SEC EDGAR, XBRL | Hệ thống nộp hồ sơ điện tử của Ủy ban Chứng khoán Hoa Kỳ và định dạng dữ liệu tài chính có cấu trúc. |
| IR | Investor Relations, trang quan hệ nhà đầu tư của công ty. |
| SRS | System Requirements Specification, đặc tả yêu cầu hệ thống. |

## 1.5 Tài liệu tham chiếu

**Tham chiếu phương pháp (Tier R, không dùng làm dữ liệu):**

| Tài liệu | URL |
| --- | --- |
| CMU/SEI — Software Requirements | `https://www.sei.cmu.edu/library/software-requirements/` |
| CMU/SEI — Software Specification: A Framework | `https://www.sei.cmu.edu/library/software-specification-a-framework/` |
| CMU/SEI — A Requirement Specification Language for AADL | `https://www.sei.cmu.edu/library/a-requirement-specification-language-for-aadl-2/` |

CMU/SEI ReqSpec đặc biệt liên quan vì liên kết đặc tả yêu cầu với kế hoạch kiểm chứng và bằng chứng rằng bản triển khai thỏa mãn yêu cầu.

> **Lưu ý kiểm chứng:** ba URL trên được giữ nguyên từ bản gốc và chưa được xác minh lại khi Việt hóa. Cần mở thủ công, ghi `access_date` vào `source_registry` trước khi nộp.

**Nguồn dữ liệu:** xem mục 3.3.

## 1.6 Quy ước viết yêu cầu **[BỔ SUNG]**

**Động từ chỉ mức bắt buộc**

| Từ dùng | Mức | Tương ứng tiếng Anh |
| --- | --- | --- |
| "phải" | Bắt buộc | shall / must |
| "nên" | Khuyến nghị | should |
| "có thể" | Tùy chọn | may |

Bản gốc dùng lẫn *shall / must / should*. Bản này thống nhất: mọi điều khoản có đánh mã yêu cầu mặc định là **bắt buộc** (phải), trừ khi ghi rõ mức khác.

**Hệ thống mã yêu cầu**

| Tiền tố | Nhóm | Mục |
| --- | --- | --- |
| RQ | Câu hỏi nghiên cứu | 2.6 |
| SRC | Nguồn và độ tin cậy | 3 |
| FR | Dữ liệu tài chính và phân khúc | 4.1–4.2 |
| AI | Đo lường AI (proxy) | 4.3 |
| OUT | Biến đầu ra | 4.4 |
| FE | Kỹ thuật đặc trưng | 4.5 |
| LAG, IO, CAU | Độ trễ, kiểm định đầu vào-đầu ra, nhân quả | 4.6 |
| EFF, SEN, ROB | Hiệu quả, độ nhạy, độ vững | 4.7–4.8 |
| EVT | Event study | 4.9 |
| REG, SCN, RSK | Regime, kịch bản, rủi ro | 4.10–4.12 |
| DEC, DSH | Quyết định, dashboard | 4.13–4.14 |
| DQ, PRV, DAT | Chất lượng dữ liệu, truy vết, dữ liệu | 5–6 |
| NFR | Yêu cầu phi chức năng | 5 |

Mỗi yêu cầu có thuộc tính tối thiểu: **mã**, **nội dung**, **căn cứ (rationale)** khi không hiển nhiên, **ưu tiên** (xem dưới) và **cách xác minh** (Phụ lục A).

**Mức ưu tiên (MoSCoW) [BỔ SUNG]:** *Must* (bắt buộc cho nghiệm thu), *Should* (nên có), *Could* (có thể có). Trừ khi ghi khác, các yêu cầu dưới đây là *Must*. **[CẦN QUYẾT ĐỊNH]** Tác giả cần rà lại các yêu cầu được đề xuất là *Should/Could*.

## 1.7 Bố cục tài liệu

| Phần | Nội dung |
| --- | --- |
| 1 | Giới thiệu |
| 2 | Mô tả tổng quan (bối cảnh, người dùng, ràng buộc, giả định, câu hỏi nghiên cứu) |
| 3 | Nguồn dữ liệu và độ tin cậy |
| 4 | Yêu cầu chức năng |
| 5 | Yêu cầu phi chức năng và chất lượng dữ liệu |
| 6 | Yêu cầu dữ liệu (cơ sở dữ liệu, từ điển đặc trưng) |
| 7 | Giao diện bên ngoài |
| 8 | Kiến trúc hệ thống |
| 9 | Xác minh và chấp nhận |
| 10 | Nguyên tắc thiết kế và tuyên bố liêm chính nghiên cứu |
| Phụ lục A | Ma trận truy vết |
| Phụ lục B | Vấn đề mở cần tác giả quyết định |

---

# 2. Mô tả tổng quan

## 2.1 Bối cảnh và mục tiêu hệ thống

Hệ thống phải trả lời câu hỏi:

> Microsoft hoặc Alphabet chuyển hóa nguồn lực liên quan đến AI thành kết quả kinh doanh và kết quả thị trường đo lường được một cách hiệu quả đến mức nào?

Chuỗi phân tích:

```text
Resources
    ↓
Investment Intensity
    ↓
AI / Cloud Business Output
    ↓
Financial Outcome
    ↓
Market Response
    ↓
Efficiency
    ↓
Regime
    ↓
Decision
```

## 2.2 Chức năng chính

| Nhóm chức năng | Mục |
| --- | --- |
| Thu thập và đăng ký nguồn dữ liệu | 3, 4.1–4.4 |
| Tính đặc trưng và hiệu quả | 4.5, 4.7 |
| Phân tích độ trễ, kiểm định đầu vào-đầu ra | 4.6 |
| Độ nhạy và độ vững | 4.8 |
| Event study, regime, kịch bản, rủi ro | 4.9–4.12 |
| Kết luận quyết định và dashboard | 4.13–4.14 |
| Kiểm soát chất lượng và truy vết dữ liệu | 5 |

## 2.3 Đối tượng sử dụng **[BỔ SUNG]**

Bản gốc không mô tả người dùng. Bản này đề xuất ba nhóm, suy ra từ Definition of Done (mục 9.3) và vai trò dashboard (mục 4.14).

| Nhóm | Nhu cầu chính |
| --- | --- |
| Reviewer (giảng viên, người chấm) | Chọn một con số trên dashboard và truy vết đến nguồn, tái lập kết quả. |
| Nhà phân tích | Xem so sánh, độ nhạy, kịch bản; đọc kết luận kèm giả định. |
| Kỹ sư dữ liệu | Nạp dữ liệu, kiểm tra chất lượng, chạy lại pipeline. |

**[CẦN QUYẾT ĐỊNH]** Xác nhận danh sách người dùng.

## 2.4 Ràng buộc

* Chỉ dùng dữ liệu công bố công khai (hồ sơ SEC, tài liệu IR chính thức, dữ liệu thị trường).
* SEC là nguồn tài chính chuẩn khi có xung đột (DQ-05).
* Không dùng ước tính của giới phân tích làm số liệu thực tế (mục 1.3.2, SRC-05).
* Chuỗi dữ liệu chỉ dài 16–20 quý cho mỗi công ty; đây là giới hạn cố hữu của phân tích.

## 2.5 Giả định và phụ thuộc **[BỔ SUNG]**

* Hồ sơ SEC EDGAR và trang IR khả dụng trong suốt thời gian thực hiện.
* Dữ liệu thị trường lấy từ Yahoo Finance, tải một lần và lưu bản gốc để cố định phiên bản (mục 3.6).
* Hai công ty có năm tài chính khác nhau (Microsoft kết thúc 30/6, Alphabet kết thúc 31/12); mọi so sánh chéo phải qua căn chỉnh quý lịch (DAT-01).
* Với 16–20 quý và độ trễ tới 4 quý, số quan sát hiệu dụng nhỏ. Kết quả thống kê phải được trình bày kèm giới hạn về cỡ mẫu (DEC-02, trường `limitations`).

## 2.6 Câu hỏi nghiên cứu

| Mã | Chủ đề | Câu hỏi |
| --- | --- | --- |
| RQ-01 | Đầu tư | Cường độ nguồn lực và đầu tư liên quan đến AI đã thay đổi thế nào theo thời gian? |
| RQ-02 | Tác động kinh doanh | Mức tăng nguồn lực liên quan đến AI có đi kèm cải thiện đầu ra kinh doanh đo lường được không? |
| RQ-03 | Hiệu quả tài chính | Công ty nào chuyển hóa nguồn lực thành doanh thu, lợi nhuận hoạt động và dòng tiền tự do hiệu quả hơn? |
| RQ-04 | Độ trễ | Quan sát được độ trễ thời gian nào giữa đầu tư và đầu ra kinh doanh? |
| RQ-05 | Thị trường | Hiệu quả kinh doanh mạnh hơn có tương ứng với abnormal return cho cổ đông không? |
| RQ-06 | Regime | Hiệu quả đầu tư giữ ổn định hay thay đổi giữa các trạng thái vận hành khác nhau? |
| RQ-07 | Độ vững | Kết luận so sánh có còn đứng vững khi thay đổi (a) định nghĩa kết quả, (b) giả định độ trễ, (c) công thức hiệu quả, (d) trọng số quyết định không? |

---

# 3. Nguồn dữ liệu và độ tin cậy

## 3.1 Mô hình độ tin cậy nguồn

**SRC-01.** Mọi nguồn phải được gán một bậc tin cậy (tier).

### Tier S — Nguồn pháp lý / nguồn tài chính gốc

Ưu tiên cao nhất.

Ví dụ: SEC EDGAR, SEC 10-Q, SEC 10-K, SEC XBRL.

Dùng cho: Revenue, Operating Income, Net Income, R&D, CFO, CapEx, Assets, Liabilities, Equity, Shares, EPS, thông tin tài chính theo phân khúc.

```text
S = authoritative financial evidence
```

### Tier A — Nguồn gốc từ công ty

Dùng nguồn chính thức của công ty cho thông tin mà hồ sơ chuẩn hóa chưa phản ánh đủ.

Ví dụ: thông cáo kết quả kinh doanh; bài thuyết trình nhà đầu tư; bản ghi cuộc họp công bố kết quả (earnings call); công bố IR chính thức; chỉ số AI/sản phẩm chính thức.

```text
A = primary corporate disclosure
```

* Microsoft Investor Relations: `https://www.microsoft.com/en-us/investor/`
* Alphabet Investor Relations: `https://abc.xyz/investor/`

Thông cáo FY26 Q3 của Microsoft báo cáo kết quả tài chính quý và thảo luận về Microsoft Cloud, Azure và hạ tầng AI. Thông cáo FY26 Q4 báo cáo kết quả quý và phân biệt rõ kết quả GAAP với các tác động liên quan đến khoản đầu tư. Tài liệu nhà đầu tư chính thức của Alphabet cung cấp kết quả thu nhập và công bố tài chính hằng quý.

### Tier B — Dữ liệu thị trường

Dùng cho: giá cổ phiếu, adjusted close, khối lượng giao dịch, lợi suất thị trường, dữ liệu benchmark.

Các trường bắt buộc:

```text
date
open
high
low
close
adjusted_close
volume
```

**SRC-02.** Dữ liệu Tier B **không được** thay thế nguồn SEC/công ty cho các biến kế toán.

### Tier R — Tham chiếu phương pháp **[BỔ SUNG]**

Bản gốc ghi các tài liệu CMU/SEI là `S-Academic`, một bậc không có trong mô hình S/A/B, trong khi tiêu chí nghiệm thu yêu cầu "mọi nguồn thuộc Tier S/A/B". Bản này định nghĩa **Tier R** cho tài liệu phương pháp luận. Tier R không dùng làm dữ liệu phân tích và nằm ngoài `source_registry` của dữ liệu tài chính.

## 3.2 Yêu cầu Source Registry

**SRC-03.** Mọi điểm dữ liệu dùng trong tầng phân tích phải truy vết được đến một nguồn.

Schema bắt buộc:

```text
source_id
company
metric
source_type
source_tier
source_url
reporting_period
filing_date
access_date
primary_or_secondary
verification_status
```

Ví dụ:

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

## 3.3 Nguồn chuẩn (canonical sources)

Bản gốc liệt kê nguồn ở hai nơi (mục 11 và mục 38). Bản này gộp thành một bảng.

| Nguồn | URL | Tier | Kỳ |
| --- | --- | --- | --- |
| Microsoft — SEC EDGAR | `https://www.sec.gov/edgar/browse/?CIK=789019` | S | — |
| Microsoft — Investor Relations | `https://www.microsoft.com/en-us/investor/` | A | — |
| Microsoft — 10-Q quý kết thúc 31/03/2026 (FY26 Q3) | `https://www.sec.gov/Archives/edgar/data/789019/000119312526191507/msft-20260331.htm` | S | 2026-03-31 |
| Microsoft — thông cáo FY26 Q3 | `https://www.microsoft.com/en-us/investor/earnings/FY-2026-Q3/press-release-webcast` | A | FY26 Q3 |
| Microsoft — thông cáo FY26 Q4 | `https://www.microsoft.com/en-us/investor/earnings/fy-2026-q4/press-release-webcast` | A | FY26 Q4 |
| Alphabet — SEC EDGAR | `https://www.sec.gov/edgar/browse/?CIK=1652044` | S | — |
| Alphabet — Investor Relations | `https://abc.xyz/investor/` | A | — |
| Alphabet — 10-Q quý kết thúc 30/06/2026 | `https://www.sec.gov/Archives/edgar/data/1652044/000165204426000071/goog-20260630.htm` | S | 2026-06-30 |
| Alphabet — tài liệu kết quả Q2 | `https://abc.xyz/investor/` | A | Q2 2026 |

10-Q quý kết thúc 31/03/2026 của Microsoft chứa báo cáo tài chính, thảo luận theo phân khúc, dữ liệu XBRL và thuyết minh về đầu tư hạ tầng AI. 10-Q quý kết thúc 30/06/2026 của Alphabet là báo cáo quý, cung cấp báo cáo tài chính hợp nhất và khung phân khúc kinh doanh.

> **Lưu ý kiểm chứng:** các URL hồ sơ SEC và trang thông cáo ở trên được giữ nguyên từ bản gốc. Chúng chưa được xác minh trong lúc Việt hóa vì không truy cập được các trang này. Mỗi URL phải được mở thủ công và ghi `verification_status` trước khi đánh dấu `verified` (SRC-03).

## 3.4 Ma trận nguồn dữ liệu

| Dữ liệu | Microsoft | Alphabet | Tier | Nguồn chuẩn |
| --- | --- | --- | --- | --- |
| Revenue | SEC 10-Q/10-K | SEC 10-Q/10-K | S | SEC |
| Gross Profit | SEC | SEC | S | SEC |
| Operating Income | SEC | SEC | S | SEC |
| Net Income | SEC | SEC | S | SEC |
| R&D | SEC | SEC | S | SEC |
| CFO | SEC | SEC | S | SEC |
| CapEx | SEC / thuyết minh dòng tiền | SEC / thuyết minh dòng tiền | S | SEC |
| Assets | SEC | SEC | S | SEC |
| Shares | SEC | SEC | S | SEC |
| EPS | SEC | SEC | S | SEC |
| Segment Revenue | SEC | SEC | S | SEC |
| Azure Growth | Microsoft IR | N/A | A | Microsoft IR |
| Microsoft Cloud Growth | Microsoft IR | N/A | A | Microsoft IR |
| Google Cloud Growth | N/A | Alphabet IR | A | Alphabet IR |
| Google Cloud Operating Income | N/A | SEC / Alphabet IR | S/A | Ưu tiên SEC |
| Stock Price | Yahoo Finance | Yahoo Finance | B | Yahoo Finance |
| Benchmark | Yahoo Finance (`^GSPC`) | Yahoo Finance (`^GSPC`) | B | S&P 500 |
| AI Event | Nguồn chính thức của công ty | Nguồn chính thức của công ty | A | Công ty |
| Filing date | SEC | SEC | S | SEC |

**Đã chốt cho giai đoạn proposal:** nhà cung cấp dữ liệu thị trường là Yahoo Finance, benchmark là S&P 500 (`^GSPC`). Lý do và cách dùng ở mục 3.6.

## 3.5 Quy tắc chọn nguồn, dữ liệu thiếu và mức tin cậy

**SRC-04 — Quy tắc chọn nguồn.** Hệ thống nạp dữ liệu phải theo:

```text
IF SEC contains metric
    USE SEC
ELSE IF official company source contains metric
    USE company source
ELSE
    SEARCH for higher-quality primary source
ELSE
    mark metric as unavailable
```

Hệ thống **không được bịa giá trị** chỉ để bảng dữ liệu đầy đủ.

**SRC-05 — Dữ liệu thiếu.** Nếu một chỉ số không có:

```text
value = NULL
status = unavailable
reason = documented
```

Không được:

```text
fill with analyst estimate
```

trừ khi nghiên cứu tạo riêng một bộ dữ liệu analyst-estimate tách biệt.

**SRC-06 — Quy tắc mức tin cậy (confidence).**

| Mức | Điều kiện | Ví dụ |
| --- | --- | --- |
| HIGH | Được báo cáo trực tiếp bởi SEC, báo cáo tài chính chính thức hoặc thông cáo kết quả chính thức. | Revenue từ 10-Q |
| MEDIUM | Suy ra từ dữ liệu nguồn có độ tin cậy cao. | `CapEx / Revenue` |
| LOW | Biến đại diện gián tiếp. | Tổng R&D làm proxy cho đầu tư AI |

**SRC-07 — Chỉ dùng dữ liệu thật có thể thu thập tự động.** Mọi biến trong phạm vi phải có nguồn thật, công khai và lấy về được bằng chương trình (SEC EDGAR/XBRL, trang IR, tệp CSV từ nhà cung cấp giá). Cụ thể:

* Không dùng dữ liệu giả (mock), dữ liệu tự bịa hoặc dữ liệu ước tính không có dẫn chứng.
* Biến nào không có nguồn thật lấy về được thì **loại khỏi phạm vi**, không tạo giá trị thay thế (xem AI-01, AI-04).
* Một quan sát đơn lẻ bị thiếu (ví dụ một quý chưa công bố) ghi `NULL` theo SRC-05, không điền số.
* Mỗi giá trị phải truy vết được đến `source_id` và `source_url` (SRC-03).

## 3.6 Dữ liệu thị trường: nhà cung cấp và benchmark

Mục này chốt hai điểm bản gốc để ngỏ (nhà cung cấp và benchmark), chọn phương án đơn giản nhất mà sinh viên làm được. Có thể đổi sau, nhưng phải ghi lại phiên bản.

**MKT-01 — Nhà cung cấp.** Dùng Yahoo Finance (Tier B), tải lịch sử giá dạng CSV hoặc bằng thư viện Python `yfinance`.

| Mã | source_url |
| --- | --- |
| MSFT | `https://finance.yahoo.com/quote/MSFT/history/` |
| GOOGL | `https://finance.yahoo.com/quote/GOOGL/history/` |
| S&P 500 (`^GSPC`) | `https://finance.yahoo.com/quote/%5EGSPC/history/` |

* Lý do chọn: miễn phí, không cần đăng ký, có `adjusted_close` (giá đã điều chỉnh cổ tức và chia tách cổ phiếu).
* Hạn chế cần ghi trong báo cáo: không phải nguồn chính thức, điều khoản sử dụng dành cho mục đích cá nhân/học tập, dữ liệu có thể được điều chỉnh về sau.

**MKT-02 — Benchmark.** Dùng S&P 500 (`^GSPC`) làm chỉ số so sánh. Benchmark chỉ là thước đo "thị trường chung", không cần cùng sàn với cổ phiếu, nên việc MSFT và GOOGL niêm yết trên NASDAQ không ngăn dùng S&P 500. Cả hai cổ phiếu đều nằm trong S&P 500.

* Giới hạn: `^GSPC` là chỉ số giá, không tính cổ tức, nên `adjusted_close` của chỉ số bằng `close`. Sai lệch nhỏ với phân tích theo quý, chấp nhận ở giai đoạn proposal.
* Tùy chọn kiểm tra độ vững: chạy lại với Nasdaq-100 (`^NDX`).

**MKT-03 — Tái lập.** Tải dữ liệu một lần, lưu file CSV gốc vào raw data layer và ghi `access_date`, nhà cung cấp, mã cổ phiếu vào `source_registry`. Không tự tải lại mỗi lần chạy, vì dữ liệu có thể thay đổi giữa hai lần tải.

**MKT-04 — Lợi suất kỳ vọng mặc định.** Dùng *market-adjusted return*:

```text
Return_t = adjusted_close_t / adjusted_close_t-1 - 1
Abnormal Return_t = Return(cổ phiếu)_t - Return(S&P 500)_t
CAR = tổng Abnormal Return trong cửa sổ [-10, +10] ngày giao dịch
```

Cách này không cần cửa sổ ước lượng nên dễ làm và dễ kiểm tra. Market model (hồi quy cổ phiếu theo thị trường) là tùy chọn nâng cao nếu còn thời gian.

---

# 4. Yêu cầu chức năng

## 4.1 Dữ liệu tài chính

**FR-01 — Revenue.** Hệ thống phải thu thập doanh thu hằng quý.

```text
field: revenue
unit: USD millions
frequency: quarterly
source_tier: S
```

**FR-02 — R&D.** Hệ thống phải thu thập chi phí R&D đã báo cáo.

```text
field: rd_expense
unit: USD millions
frequency: quarterly
source_tier: S
```

R&D **không** được tự động xếp vào loại đầu tư AI.

**FR-03 — CapEx.** Hệ thống phải thu thập chi tiêu vốn hoặc chi tiêu vốn bằng tiền theo một định nghĩa kế toán nhất quán.

```text
field: capex
unit: USD millions
frequency: quarterly
source_tier: S
```

Nếu nguồn báo cáo CapEx theo định nghĩa riêng của công ty, định nghĩa đó phải được giữ lại.

**FR-04 — Operating Income.**

```text
field: operating_income
unit: USD millions
frequency: quarterly
source_tier: S
```

**FR-05 — Free Cash Flow.** Định nghĩa ưu tiên:

```text
FCF = CFO - CapEx
```

Định nghĩa phải được lưu cùng giá trị.

## 4.2 Dữ liệu phân khúc

**FR-06 — Microsoft.** Bắt buộc có:

```text
Intelligent Cloud Revenue
Azure Growth
Microsoft Cloud Revenue
Productivity & Business Processes Revenue
```

Công bố chính thức của Microsoft xác định Azure và Microsoft Cloud là các động lực tăng trưởng quan trọng gần đây.

**FR-07 — Alphabet.** Bắt buộc có:

```text
Google Services Revenue
Google Cloud Revenue
Google Cloud Operating Income
Google Services Operating Income
```

Tài liệu chính thức của Alphabet báo cáo riêng Google Services và Google Cloud, đồng thời thảo luận tăng trưởng Cloud, hạ tầng AI và khả năng sinh lời.

## 4.3 Đặc tả đo lường AI

**AI-01 — Đã loại khỏi phạm vi.** Không thu thập "đầu tư AI" trực tiếp, vì không có dữ liệu thật lấy về được theo quý (SRC-07). Mã được giữ để các tham chiếu cũ không bị gãy. Chỉ dùng proxy (AI-02).

**AI-02 — Biến đại diện đầu tư AI.** Vì không có số liệu đầu tư AI trực tiếp, mọi biến đầu tư AI đều là proxy:

```text
reported = false
derived = true
proxy = true
```

Các proxy có thể dùng:

```text
R&D
CapEx
R&D / Revenue
CapEx / Revenue
CapEx Growth
R&D Growth
```

**AI-03 — Nhãn hiển thị.** Dashboard phải hiển thị:

> **AI Investment Proxy**

và không hiển thị:

> **AI Investment**

### 4.3.1 Hướng dẫn dùng proxy đầu tư AI (dành cho người mới)

**Phạm vi hiện tại.** Không có con số "đầu tư AI" trực tiếp theo quý để lấy về, nên dự án chỉ dùng proxy thật (AI-02, SRC-07).

**Hai proxy sẽ dùng**

| Proxy | Là gì | Tìm ở đâu trong hồ sơ 10-Q | Liên quan đến AI thế nào | Độ tin cậy |
| --- | --- | --- | --- | --- |
| CapEx (proxy chính) | Tiền chi để mua hoặc xây tài sản dùng nhiều năm: trung tâm dữ liệu, máy chủ, chip. | Báo cáo lưu chuyển tiền tệ (Cash Flow Statement), dòng chi mua tài sản cố định. Tên dòng khác nhau theo công ty, ví dụ "Additions to property and equipment" hoặc "Purchases of property and equipment". Cần mở hồ sơ để xác nhận. | Hai công ty đều nói đang chi để xây hạ tầng AI và đám mây, nhưng CapEx còn gồm cả khoản không liên quan AI. | MEDIUM (suy ra, gián tiếp) |
| R&D (proxy phụ) | Chi phí nghiên cứu và phát triển. | Báo cáo kết quả kinh doanh (Income Statement), dòng "Research and development". | Gồm toàn bộ R&D của công ty, không riêng AI. | LOW |

**Chuẩn hóa.** Hai công ty khác quy mô nên không so sánh số tuyệt đối. Chia cho doanh thu cùng quý: `CapEx / Revenue` và `R&D / Revenue` (FE-03, FE-04).

**Bẫy dữ liệu theo quý (DQ-03).**
* Báo cáo lưu chuyển tiền tệ trong 10-Q thường là số **cộng dồn từ đầu năm tài chính** (YTD). CapEx quý 2 = số 6 tháng trừ số quý 1; quý 3 = số 9 tháng trừ số 6 tháng.
* Quý 4 không có 10-Q. Lấy số cả năm trong 10-K trừ số 9 tháng.
* Báo cáo kết quả kinh doanh (Revenue, R&D) trong 10-Q có cột "Three Months Ended" cho đúng quý, nhưng quý 4 vẫn phải tính bằng số cả năm trừ 9 tháng.
* Với Microsoft, năm tài chính bắt đầu từ tháng 7, nên "quý 1" là tháng 7–9. Làm theo cùng quy tắc, rồi căn chỉnh quý lịch (DAT-01).

**Định nghĩa CapEx phải nhất quán (FR-03).** Dùng một định nghĩa duy nhất cho cả hai công ty: tiền chi mua tài sản cố định ghi ở báo cáo lưu chuyển tiền tệ. Định nghĩa này không gồm hợp đồng thuê tài chính (finance lease), nên có thể thấp hơn con số "CapEx gồm thuê tài chính" mà công ty nhắc trong thông cáo. Ghi giới hạn này vào `definition`.

**Cách viết kết luận.** Luôn ghi "CapEx (proxy)", không viết "đầu tư AI". Ví dụ đúng: "CapEx/Revenue của Microsoft tăng trong khi Azure growth cũng tăng". Ví dụ sai: "đầu tư AI làm Azure tăng trưởng" (vi phạm CAU-01).

**Việc tối thiểu cho mỗi công ty và mỗi quý**
1. Mở 10-Q hoặc 10-K của quý đó (mục 3.3).
2. Lấy ba con số: Revenue, R&D, CapEx. Ghi rõ số đó là "ba tháng" hay "cộng dồn".
3. Nếu là cộng dồn, trừ đi để ra số một quý.
4. Ghi vào bảng kèm `source_url` và tên báo cáo chứa con số (đây là `source_registry`).
5. Tính `CapEx / Revenue` và `R&D / Revenue`, gán nhãn proxy.

## 4.4 Biến đầu ra

### AI-04 — Đã loại khỏi phạm vi

Bản gốc có nhóm "biến phơi nhiễm AI" (`ai_services_growth`, `ai_infrastructure_disclosure`, `copilot_metric`, `gemini_metric`, `ai_compute_disclosure`). Các chỉ số này không được công bố đều đặn dạng số, nên không có dữ liệu thật để thu thập tự động. Hai biến còn lại (`azure_growth`, `google_cloud_growth` và các biến Cloud tương tự) vốn là đầu ra (OUT-01).

Hệ quả: biến đầu vào của phân tích chỉ là proxy thật (CapEx, R&D và các tỷ số của chúng). Cách này cũng xử lý luôn vấn đề đầu vào và đầu ra trùng nhau (B-02).

### OUT-01 — Đầu ra kinh doanh

**Microsoft**

```text
azure_growth
microsoft_cloud_growth
intelligent_cloud_growth
productivity_growth
```

**Alphabet**

```text
google_cloud_growth
google_cloud_operating_income_growth
google_services_growth
```

### OUT-02 — Đầu ra tài chính

Áp dụng cho cả hai công ty:

```text
revenue_growth
operating_income_growth
operating_margin
fcf_growth
eps_growth
```

Đây là kết quả ở cấp công ty. Không được diễn giải chúng như kết quả thuần túy của AI.

### OUT-03 — Đầu ra thị trường

Bắt buộc có:

```text
quarter_return
forward_quarter_return
volatility
maximum_drawdown
abnormal_return
```

Đầu ra thị trường chính:

```text
forward_1_quarter_abnormal_return
```

## 4.5 Kỹ thuật đặc trưng (Feature Engineering)

**FE-01 — YoY Growth.** Ưu tiên dùng để so sánh theo quý.

```text
YoY Growth = (Value_t / Value_t-4) - 1
```

**FE-02 — QoQ Growth.** Dùng thận trọng vì tính mùa vụ.

```text
QoQ Growth = (Value_t / Value_t-1) - 1
```

**FE-03 — R&D Intensity.**

```text
R&D Intensity = R&D / Revenue
```

**FE-04 — CapEx Intensity.**

```text
CapEx Intensity = CapEx / Revenue
```

**FE-05 — Revenue Efficiency.** Đây là tỷ số phân tích, không phải ROI kế toán.

```text
Revenue Efficiency = Revenue Growth / Resource Growth
```

**FE-06 — Operating Efficiency.**

```text
Operating Efficiency = Operating Income Growth / Resource Growth
```

**FE-07 — FCF Efficiency.**

```text
FCF Efficiency = FCF Growth / Resource Growth
```

**FE-08 — Điều kiện áp dụng công thức tăng trưởng và hiệu quả [BỔ SUNG].** Các công thức FE-01, FE-05, FE-06, FE-07 không xác định hoặc vô nghĩa khi:

* mẫu số `Resource Growth` bằng 0 hoặc rất gần 0;
* giá trị gốc (`Value_t-4` hoặc `Value_t-1`) bằng 0 hoặc âm. Trường hợp đáng chú ý: FCF có thể âm khi CapEx vượt CFO, khiến `fcf_growth` mất ý nghĩa.

Hệ thống phải gán `NULL` kèm lý do (theo SRC-05) cho các trường hợp trên và không được chặn cận hay làm tròn để che đi. Ngưỡng "rất gần 0" phải được cấu hình và lưu cùng phiên bản.

## 4.6 Phân tích độ trễ, kiểm định và ràng buộc nhân quả

**LAG-01 — Độ trễ cần kiểm định.** Hệ thống phải kiểm định:

```text
lag_0
lag_1
lag_2
lag_3
lag_4
```

Ví dụ chuỗi độ trễ:

```text
CapEx(t)
   ↓
Azure / Cloud Growth(t+1)
   ↓
Revenue(t+2)
   ↓
Operating Income(t+2/t+3)
   ↓
Market Response(t+2/t+3)
```

**LAG-02.** Hệ thống không được giả định độ trễ trước khi phân tích.

**IO-01 — Các quan hệ đầu vào → đầu ra cần kiểm định.**

```text
CapEx Growth → Cloud Growth
R&D Growth → Cloud Growth
R&D Intensity → Revenue Growth
CapEx Intensity → Operating Margin
```

Mỗi quan hệ phải được kiểm định với `lag = 0, 1, 2, 3, 4`.

**IO-02 — Phương pháp thống kê [BỔ SUNG, CẦN QUYẾT ĐỊNH].** Bản gốc không nêu phương pháp ước lượng (tương quan, hồi quy có độ trễ, kiểm định Granger…). Yêu cầu `Lag analysis` phải "tái lập được" (mục 9.1) chỉ kiểm chứng được khi phương pháp, tham số và hạt giống ngẫu nhiên (nếu có) được ghi vào `analysis_results.method`. Xem B-04.

**CAU-01 — Ràng buộc nhân quả.** AICOR phải phân biệt:

```text
Association
Correlation
Temporal relationship
Causal claim
```

Cách diễn đạt mặc định của đầu ra là:

> associated with (có liên hệ với)

và không phải:

> caused (gây ra)

trừ khi bằng chứng và thiết kế nghiên cứu biện minh cho cách diễn giải nhân quả.

## 4.7 Mô hình hiệu quả

**EFF-01 — Nhiều thước đo.** Hệ thống phải tính nhiều thước đo hiệu quả:

```text
Revenue Efficiency
Operating Income Efficiency
FCF Efficiency
Market Efficiency
Rolling Efficiency
```

Điểm tổng hợp chỉ được xây dựng sau khi các thước đo riêng lẻ đã được hiển thị.

**EFF-02 — Điểm hiệu quả tổng hợp (Composite Efficiency Score).** Đặc tả ban đầu:

```text
Efficiency Score =
  0.30 × Revenue Efficiency
+ 0.30 × Operating Efficiency
+ 0.25 × FCF Efficiency
+ 0.15 × Market Efficiency
```

Các trọng số có thể cấu hình (tổng bằng 1,00). Hệ thống phải lưu:

```text
weight_version
weights
normalization_method
```

> **[CẦN QUYẾT ĐỊNH] (B-03).** `normalization_method` chưa được định nghĩa, trong khi bốn thước đo có thang đo khác nhau (tỷ số tăng trưởng, abnormal return). Cần chốt cách chuẩn hóa (z-score, min–max, xếp hạng phân vị…) trước khi cộng có trọng số.

## 4.8 Độ nhạy và độ vững

**SEN-01 — Phân tích độ nhạy.** Hệ thống phải lặp lại phân tích với:

*Kết quả (outcomes):*

```text
Revenue Growth
Operating Income Growth
FCF Growth
Abnormal Return
```

*Độ trễ (lags):*

```text
0
1
2
3
4
```

> **Đã sửa:** bản gốc liệt kê `0, 1, 2, 4` ở mục này, thiếu `3`, mâu thuẫn với LAG-01, IO-01 và tiêu chí nghiệm thu "Lag 0–4 tested".

*Công thức hiệu quả:*

```text
Revenue-based
Operating-income-based
FCF-based
Market-based
```

*Trọng số quyết định, tối thiểu gồm:*

```text
Baseline
Financial-heavy
Efficiency-heavy
Market-heavy
Risk-heavy
```

**ROB-01 — Phân loại độ vững.**

Nếu thứ hạng công ty không đổi **trên mọi cấu hình của SEN-01**:

```text
ROBUST
```

Nếu thứ hạng thay đổi ở ít nhất một cấu hình:

```text
SENSITIVE
```

Hệ thống phải báo cáo nguồn gây nhạy cảm. Ví dụ:

```text
Winner:
Microsoft

Status:
SENSITIVE

Reason:
Ranking reverses when lag changes from 1 to 4 quarters.
```

## 4.9 Event study

**EVT-01 — Loại sự kiện và trường dữ liệu.**

Loại sự kiện bắt buộc:

```text
AI Model Launch
AI Product Launch
AI Partnership
AI Infrastructure Announcement
Earnings Release
AI Acquisition
Major AI Investment
Regulatory Event
```

Trường của sự kiện:

```text
event_id
company
event_date
event_type
description
source_url
source_tier
```

**EVT-02 — Quy tắc nguồn của sự kiện.** Sự kiện phải lấy từ:

1. thông báo chính thức của công ty;
2. hồ sơ SEC;
3. thông báo chính thức của cơ quan quản lý.

Truyền thông tin tức chỉ được dùng làm bối cảnh bổ trợ. Bản thân sự kiện nên truy vết được đến nguồn gốc bất cứ khi nào có thể.

**EVT-03 — Cửa sổ sự kiện thị trường.** Mặc định:

```text
[-10, +10] trading days
```

Phải tính:

```text
Expected Return
Abnormal Return
CAR
```

Benchmark phải được chỉ định rõ và đánh số phiên bản.

> **Mặc định cho proposal (B-05):** dùng market-adjusted return so với S&P 500 (MKT-04), không cần cửa sổ ước lượng. Market model là tùy chọn nâng cao.

## 4.10 Nhận diện regime

**REG-01.** Các regime bắt buộc:

```text
Efficient Expansion
Investment Pressure
Efficiency
Slowdown
```

Việc phân loại phải dựa trên:

```text
Investment Intensity
Business Output
Financial Efficiency
```

Cách triển khai ưu tiên:

```text
Rolling Efficiency
+
Threshold Classification
```

Tùy chọn:

```text
Change-point Detection
Clustering
```

> **[CẦN QUYẾT ĐỊNH] (B-06).** (a) Tên regime thứ ba, `Efficiency`, trùng với tên của một nhóm thước đo (EFF-01) và không mô tả một trạng thái riêng; bản này giữ nguyên tên gốc để tác giả chốt. (b) Chưa có ngưỡng phân loại, nên yêu cầu chưa kiểm chứng được. Cần định nghĩa ngưỡng hoặc bảng quyết định giữa ba biến đầu vào và bốn regime.

## 4.11 Phân tích kịch bản

**SCN-01 — Investment Acceleration (S1).**

```text
CapEx +20%
R&D +10%
```

**SCN-02 — Monetization Slowdown (S2).**

```text
Cloud Growth -10%
```

**SCN-03 — Productivity Improvement (S3).**

```text
Revenue / R&D +15%
```

Mọi giá trị kịch bản là:

```text
ASSUMPTIONS
```

không phải hướng dẫn (guidance) của công ty.

## 4.12 Rủi ro

**RSK-01.** Các biến rủi ro:

```text
Investment Intensity
Margin Pressure
FCF Pressure
CapEx Acceleration
Revenue Deceleration
Efficiency Decline
Volatility
Drawdown
```

Hệ thống phải phân biệt:

```text
High Investment + High Output
```

với:

```text
High Investment + Weak Output
```

Sự phân biệt này là trung tâm của cách diễn giải kinh doanh của dự án. *(Bản gốc dùng "should"; bản này nâng lên "phải" vì điều khoản được mô tả là trung tâm.)*

## 4.13 Đầu ra quyết định

**DEC-01 — Kết quả có cấu trúc cho từng công ty.**

```yaml
company: MSFT
financial_score: ...
ai_efficiency_score: ...
market_score: ...
risk_score: ...
composite_score: ...
ranking: ...
robustness: ...
confidence: ...
```

và bản ghi tương đương cho Alphabet.

> **[CẦN QUYẾT ĐỊNH] (B-03).** `composite_score` ở đây kết hợp bốn điểm (financial, ai_efficiency, market, risk), nhưng EFF-02 chỉ định nghĩa một `Efficiency Score` gồm bốn thước đo hiệu quả và không có thành phần rủi ro. Công thức và trọng số của `composite_score`, cũng như ý nghĩa của các bộ trọng số "Financial-heavy… Risk-heavy" trong SEN-01, chưa được định nghĩa.

**DEC-02 — Bản ghi quyết định.** Hệ thống cũng phải tạo:

```yaml
decision:
winner: ...
confidence: ...
robustness: ...
key_drivers:
  - ...
  - ...
  - ...
sensitivity:
  - ...
limitations:
  - ...
```

**DEC-03 — Quy tắc diễn giải.** Hệ thống nên ưu tiên các câu như:

> "Microsoft cho thấy hiệu quả vận hành cao hơn dưới đặc tả độ trễ 2 quý."

thay vì:

> "AI của Microsoft tốt hơn."

Ưu tiên:

> "Dữ liệu quan sát nhất quán với việc chuyển hóa cường độ đầu tư thành tăng trưởng đám mây mạnh hơn."

thay vì:

> "Đầu tư AI đã gây ra tăng trưởng doanh thu."

Hệ thống phải giữ sự phân biệt giữa:

```text
Observed fact
Derived metric
Association
Interpretation
Scenario
```

## 4.14 Dashboard

**DSH-01 — Hợp đồng dashboard.** Dashboard nằm phía hạ nguồn của hệ thống nghiên cứu. Nó phải đọc từ:

```text
features_quarterly
analysis_results
scenario_results
source_registry
data_quality_log
```

Dashboard không được tự tính các số liệu tài chính từ số nhập tay.

**DSH-02 — Các trang bắt buộc.**

```text
01 — Executive Comparison
02 — Investment
03 — Business Impact
04 — Lag Analysis
05 — Efficiency
06 — Market Response
07 — Efficiency Regimes
08 — Scenario Analysis
09 — Evidence & Provenance
```

---

# 5. Yêu cầu phi chức năng và chất lượng dữ liệu

## 5.1 Chất lượng dữ liệu

**DQ-01 — Tính đầy đủ (Completeness).**

```text
missing_rate < configurable_threshold
```

**DQ-02 — Tính hợp lệ (Validity).** Ví dụ:

```text
Revenue >= 0
CapEx >= 0
Shares > 0
```

> **Ghi chú [BỔ SUNG]:** báo cáo lưu chuyển tiền tệ thường ghi CapEx là số âm (dòng tiền ra). Quy ước dấu phải được thống nhất tại bước nạp và ghi trong `definition` của FR-03 để `CapEx >= 0` kiểm tra đúng.

**DQ-03 — Nhất quán kỳ báo cáo.** Không được trộn dữ liệu:

```text
Quarterly
```

với:

```text
Year-to-Date
```

nếu không có phép biến đổi rõ ràng.

**DQ-04 — Đối chiếu kế toán.** Khi áp dụng được:

```text
Assets = Liabilities + Equity
```

**DQ-05 — Đối chiếu nguồn.** So sánh:

```text
SEC
vs.
Company IR
```

Nếu xung đột:

```text
SEC = canonical financial source
```

## 5.2 Hợp đồng truy vết (Provenance Contract)

**PRV-01.** Mọi đặc trưng (feature) phải có:

```text
feature_id
company
period
value
unit
definition
source_id
source_url
source_tier
reported_or_derived
proxy
calculation_method
confidence
```

Ví dụ:

```yaml
feature_id: MSFT_CAPEX_INTENSITY_2026Q3
company: MSFT
period: 2026Q3
value: 0.XX
unit: ratio
definition: "CapEx divided by quarterly revenue"
source_id: MSFT_SEC_10Q_2026Q3
source_url: https://www.sec.gov/Archives/edgar/data/789019/000119312526191507/msft-20260331.htm
source_tier: S
reported_or_derived: derived
proxy: false
calculation_method: "capex / revenue"
confidence: HIGH
```

## 5.3 Yêu cầu phi chức năng **[BỔ SUNG]**

Các yêu cầu dưới đây được rút ra từ nguyên tắc thiết kế (mục 10) và Definition of Done (mục 9.3) của bản gốc, đặt thành yêu cầu có thể kiểm chứng.

| Mã | Yêu cầu | Căn cứ | Xác minh |
| --- | --- | --- | --- |
| NFR-01 | **Tái lập (reproducibility).** Với cùng dữ liệu đầu vào và cùng phiên bản cấu hình, hệ thống phải cho ra cùng kết quả phân tích. | Mục 10, 9.3 | Chạy lại pipeline, so sánh `analysis_results` |
| NFR-02 | **Truy vết (traceability).** Từ mọi con số chính trên dashboard phải lần được ngược đến `source_id` và `source_url`. | Mục 9.3 | Kiểm tra `source_id → source_url` |
| NFR-03 | **Quản lý phiên bản cấu hình.** Trọng số, benchmark, ngưỡng và công thức phải có `version` và được lưu cùng kết quả. | EFF-02, EVT-03 | Kiểm tra schema |
| NFR-04 | **Minh bạch giả định.** Mọi kết luận phải đi kèm các giả định mà nó phụ thuộc. | Mục 10 | Rà soát DEC-02 |

**[CẦN QUYẾT ĐỊNH] (B-08).** Bản gốc chưa có yêu cầu về hiệu năng, bảo mật, khả dụng/giao diện hay khả năng bảo trì. Nếu đồ án bắt buộc dùng các đặc tính chất lượng theo ISO/IEC 25010, cần bổ sung nhóm NFR tương ứng.

---

# 6. Yêu cầu dữ liệu

## 6.1 Căn chỉnh quý giữa hai công ty **[BỔ SUNG]**

**DAT-01.** Microsoft có năm tài chính kết thúc ngày 30/6, Alphabet kết thúc ngày 31/12. Quý tài chính của hai công ty do đó lệch nhau: quý kết thúc 31/03/2026 là FY26 Q3 của Microsoft nhưng là Q1 của Alphabet. Bản gốc dùng "Công ty × Quý tài chính" làm đơn vị phân tích nhưng không nêu quy tắc căn chỉnh, và ví dụ của nó gán nhãn `2026Q3` cho quý kết thúc 31/03/2026 của Microsoft trong khi Alphabet "Q2" kết thúc ngày 30/06/2026.

Hệ thống phải:

* lưu `period_end_date` (ngày kết thúc quý) làm khóa so sánh chéo;
* lưu `fiscal_period` (nhãn quý tài chính của từng công ty) chỉ để hiển thị và đối chiếu nguồn;
* khi so sánh hai công ty hoặc tính độ trễ chung, ghép theo quý lịch (calendar quarter) suy ra từ `period_end_date`.

**[CẦN QUYẾT ĐỊNH] (B-09).** Xác nhận quy tắc căn chỉnh quý lịch.

## 6.2 Đặc tả cơ sở dữ liệu

Các thay đổi so với bản gốc được đánh dấu bằng **(sửa)** hoặc **(thêm)**.

### `companies`

```text
company_id
company_name
ticker
exchange
fiscal_year_end
business_description
```

### `financial_quarterly`

```text
company_id
period                (nhãn quý tài chính)
period_end_date       (thêm — xem DAT-01)
revenue
gross_profit
operating_income
net_income
rd_expense            (sửa — bản gốc dùng "rd", không khớp FR-02)
cfo
capex
fcf
assets
liabilities
equity
shares
eps
source_id
```

### `segments_quarterly`

```text
company_id
period
period_end_date       (thêm)
segment
revenue
operating_income
growth
source_id
```

### `market_daily`

```text
company_id
date
open
high
low
close
adjusted_close
volume
source_id
```

### `ai_metrics`

```text
company_id
period
period_end_date       (thêm)
metric
value
unit
reported_or_derived
proxy
confidence
source_id
```

### `ai_events`

```text
event_id
company_id
event_date
event_type
description
source_id
```

### `features_quarterly`

```text
feature_id            (thêm — theo PRV-01)
company_id
period
period_end_date       (thêm)
feature
value
unit                  (thêm — theo PRV-01)
definition
calculation_method
reported_or_derived   (thêm — theo PRV-01)
proxy                 (thêm — theo PRV-01)
confidence
source_id
```

`source_url` và `source_tier` được lấy qua khóa `source_id` từ `source_registry`.

### `analysis_results`

```text
analysis_id
company_id
period
analysis_type
metric
value
lag
method
confidence
```

### `scenario_results`

```text
scenario_id
company_id
assumption
financial_effect
efficiency_effect
risk_effect
```

### `source_registry`

```text
source_id
company
metric
source_type
source_tier
source_url
reporting_period
filing_date
access_date
primary_or_secondary  (thêm — bản gốc có ở SRC-03 nhưng thiếu ở bảng này)
verification_status
```

### `data_quality_log`

```text
check_id
company
period
check_type
status
severity
description
```

## 6.3 Từ điển đặc trưng cốt lõi

| Đặc trưng | Định nghĩa | Nguồn | Tier | Derived |
| --- | --- | --- | --- | --- |
| Revenue | Doanh thu quý đã báo cáo | SEC | S | Không |
| R&D | Chi phí R&D đã báo cáo | SEC | S | Không |
| CapEx | Chi tiêu vốn | SEC | S | Không |
| Operating Income | Lợi nhuận hoạt động đã báo cáo | SEC | S | Không |
| FCF | CFO − CapEx | SEC | S | Có |
| R&D / Revenue | R&D chia Revenue | SEC | S | Có |
| CapEx / Revenue | CapEx chia Revenue | SEC | S | Có |
| Azure Growth | Tăng trưởng Azure đã báo cáo | Microsoft IR | A | Không |
| Microsoft Cloud Growth | Tăng trưởng Microsoft Cloud đã báo cáo | Microsoft IR | A | Không |
| Google Cloud Growth | Tăng trưởng Cloud đã báo cáo | Alphabet IR | A | Không |
| Google Cloud Op. Income | Lợi nhuận hoạt động Cloud đã báo cáo | SEC / Alphabet IR | S/A | Không |
| AI Investment Proxy | Proxy được gán nhãn rõ | Derived | Kế thừa tier nguồn gốc (S) | Có |
| Stock Return | Lợi suất thị trường | Nhà cung cấp thị trường | B | Có |
| Abnormal Return | Lợi suất trừ lợi suất kỳ vọng | Nhà cung cấp thị trường | B | Có |

> **Đã sửa:** bản gốc ghi tier của `AI Investment Proxy` là "—", mâu thuẫn với tiêu chí "mọi nguồn có phân loại Tier" và "chỉ số suy ra giữ nguồn gốc của nó". Tier nay kế thừa từ dữ liệu gốc tạo ra proxy.

---

# 7. Giao diện bên ngoài **[BỔ SUNG]**

Bản gốc không có mục này. Nội dung dưới đây chỉ tổng hợp từ các mục có sẵn.

| Giao diện | Mô tả | Yêu cầu liên quan |
| --- | --- | --- |
| SEC EDGAR / XBRL | Nguồn dữ liệu tài chính chuẩn (Tier S). | SRC-01, SRC-04, DQ-05 |
| Trang Investor Relations | Nguồn chỉ số vận hành Cloud (Azure, Microsoft Cloud, Google Cloud) (Tier A). | SRC-01, FR-06, FR-07 |
| Yahoo Finance | Giá, khối lượng, benchmark S&P 500 (Tier B). | SRC-02, MKT-01 … MKT-04, EVT-03 |
| Dashboard (chín trang) | Giao diện người dùng, chỉ đọc từ cơ sở dữ liệu. | DSH-01, DSH-02 |

---

# 8. Kiến trúc hệ thống

```text
                    ┌─────────────────────┐
                    │   PRIMARY SOURCES   │
                    │ SEC / Company IR    │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │   SOURCE REGISTRY   │
                    │ URL / Tier / Period │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │    RAW DATA LAYER   │
                    │ Financial / Market  │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │    DATA QUALITY     │
                    │ Validate / Reconcile│
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │ FEATURE ENGINEERING │
                    │ Growth / Intensity  │
                    └──────────┬──────────┘
                               │
                               ↓
             ┌────────────────────────────────┐
             │       ANALYTICAL ENGINE        │
             │                                │
             │ Input → Output                 │
             │ Lag Analysis                   │
             │ Efficiency                     │
             │ Event Study                    │
             │ Regime Analysis                │
             │ Sensitivity                    │
             │ Scenario                       │
             └───────────────┬────────────────┘
                             │
                             ↓
                    ┌─────────────────────┐
                    │   DECISION ENGINE   │
                    │ Score / Risk /      │
                    │ Robustness          │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │      DASHBOARD      │
                    │ Evidence → Decision │
                    └─────────────────────┘
```

Tên các khối được giữ nguyên tiếng Anh để khớp với tên module trong mã nguồn.

---

# 9. Xác minh và chấp nhận

## 9.1 Ma trận xác minh

| Yêu cầu | Mã | Phương pháp xác minh |
| --- | --- | --- |
| Dữ liệu tài chính có nguồn | SRC-03 | Kiểm toán source registry |
| Dữ liệu SEC là chuẩn | DQ-05 | Đối chiếu chéo nguồn |
| Gán nhãn proxy | AI-02, AI-03 | Kiểm tra schema |
| Nhất quán theo quý | DQ-03, DAT-01 | Kiểm tra kỳ báo cáo |
| Đúng đắn của chỉ số suy ra | FE-01 … FE-08 | Kiểm thử công thức |
| Phân tích độ trễ | LAG-01, IO-01 | Tính toán tái lập được |
| Event study | EVT-01 … EVT-03 | Kiểm toán sự kiện/nguồn |
| Dashboard đúng | DSH-01 | Đối chiếu dashboard với cơ sở dữ liệu |
| Độ vững của quyết định | SEN-01, ROB-01 | Độ nhạy theo trọng số |
| Truy vết nguồn | PRV-01, NFR-02 | Kiểm tra `source_id → source_url` |

## 9.2 Tiêu chí chấp nhận

Bản triển khai không được xem là hoàn thành trừ khi đạt toàn bộ các tiêu chí sau.

**Dữ liệu**

* [ ] Thu thập 16–20 quý khi có thể. (FR-01 … FR-05)
* [ ] Có nguồn SEC cho báo cáo tài chính. (SRC-04)
* [ ] Có nguồn IR của công ty cho các chỉ số vận hành đặc thù. (SRC-04, FR-06, FR-07)
* [ ] Có dữ liệu thị trường cho giai đoạn phân tích. (SRC-02)
* [ ] Mọi quan sát có `source_id`. (SRC-03)
* [ ] Dữ liệu hai công ty được căn chỉnh theo quý lịch. (DAT-01) **[BỔ SUNG]**
* [ ] Mọi giá trị đều lấy từ nguồn thật; không có dữ liệu mock hay ước tính. (SRC-07)

**Đo lường**

* [ ] Đầu tư AI không bao giờ được trình bày như một sự kiện kế toán chung. (AI-02, AI-03)
* [ ] Các proxy AI đều được gán nhãn. (AI-02)
* [ ] Đầu ra "gần AI" được tách khỏi đầu ra toàn công ty. (OUT-01, OUT-02)

**Phân tích**

* [ ] Đã tính các đặc trưng tăng trưởng. (FE-01, FE-02)
* [ ] Đã tính cường độ đầu tư. (FE-03, FE-04)
* [ ] Đã tính các thước đo hiệu quả. (FE-05 … FE-07, EFF-01)
* [ ] Đã kiểm định lag 0–4. (LAG-01, IO-01)
* [ ] Đã triển khai event study. (EVT-01 … EVT-03)
* [ ] Đã triển khai phân tích regime. (REG-01)
* [ ] Đã triển khai phân tích kịch bản. (SCN-01 … SCN-03)

**Độ vững**

* [ ] Hoàn thành độ nhạy theo kết quả. (SEN-01)
* [ ] Hoàn thành độ nhạy theo độ trễ. (SEN-01)
* [ ] Hoàn thành độ nhạy theo trọng số. (SEN-01)
* [ ] Sinh trạng thái Robust/Sensitive. (ROB-01)

**Truy vết**

* [ ] Mọi chỉ số chính có `source_url`. (PRV-01)
* [ ] Mọi nguồn dữ liệu có phân loại Tier S/A/B. (SRC-01)
* [ ] Chỉ số suy ra giữ được nguồn gốc của nó. (PRV-01)
* [ ] Chỉ số proxy không thể bị hiển thị như chỉ số báo cáo trực tiếp. (AI-03)

## 9.3 Định nghĩa hoàn thành (Definition of Done)

AICOR hoàn thành khi một reviewer có thể chọn bất kỳ con số chính nào trên dashboard và truy vết:

```text
Dashboard
    ↓
Analysis Result
    ↓
Feature
    ↓
Calculation
    ↓
Raw Data
    ↓
Source ID
    ↓
Source URL
    ↓
SEC / Official Company Disclosure
```

rồi tự tái lập được kết quả.

Khả năng truy vết đó là tiêu chí chấp nhận cốt lõi của hệ thống.

---

# 10. Nguyên tắc thiết kế và tuyên bố liêm chính nghiên cứu

## 10.1 Nguyên tắc thiết kế cốt lõi

Dự án không tối ưu theo số lượng biểu đồ. Dự án tối ưu theo chuỗi:

```text
Evidence
    ↓
Traceability
    ↓
Reproducibility
    ↓
Analytical validity
    ↓
Decision usefulness
```

Quy tắc quan trọng nhất:

> **Mọi con số quan trọng phải truy vết được đến một nguồn đáng tin cậy, mọi con số suy ra phải công bố công thức của nó, và mọi kết luận phải công bố các giả định mà nó đứng vững dưới.**

## 10.2 Tuyên bố liêm chính nghiên cứu

AICOR là một phân tích so sánh dựa trên dữ liệu công ty được công bố công khai.

Hệ thống không tuyên bố quan sát được toàn bộ khoản đầu tư AI nội bộ của cả hai công ty.

Khi không có dữ liệu đầu tư AI trực tiếp, hệ thống dùng các proxy được gán nhãn rõ và báo cáo mức bất định phát sinh.

Do đó hệ thống đánh giá:

> **mức độ phơi nhiễm đầu tư liên quan đến AI quan sát được, và mối liên hệ của nó với các kết quả kinh doanh quan sát được**

thay vì tuyên bố đo được một "ROI thực của AI" không quan sát được.

---

# Phụ lục A — Ma trận truy vết **[BỔ SUNG]**

| Câu hỏi nghiên cứu | Yêu cầu | Bảng dữ liệu | Trang dashboard |
| --- | --- | --- | --- |
| RQ-01 Đầu tư | FR-02, FR-03, AI-02, FE-03, FE-04 | `financial_quarterly`, `features_quarterly` | 02 |
| RQ-02 Tác động kinh doanh | OUT-01, OUT-02, IO-01, FE-01 | `features_quarterly`, `analysis_results` | 03 |
| RQ-03 Hiệu quả tài chính | FE-05 … FE-07, EFF-01, EFF-02 | `features_quarterly`, `analysis_results` | 05 |
| RQ-04 Độ trễ | LAG-01, LAG-02, IO-01, IO-02 | `analysis_results` | 04 |
| RQ-05 Thị trường | OUT-03, EVT-01 … EVT-03 | `market_daily`, `ai_events`, `analysis_results` | 06 |
| RQ-06 Regime | REG-01, EFF-01 (Rolling Efficiency) | `analysis_results` | 07 |
| RQ-07 Độ vững | SEN-01, ROB-01, DEC-01, DEC-02 | `analysis_results`, `scenario_results` | 01, 08 |
| (Kịch bản và rủi ro) | SCN-01 … SCN-03, RSK-01 | `scenario_results` | 08 |
| (Truy vết) | SRC-03, PRV-01, DQ-01 … DQ-05 | `source_registry`, `data_quality_log` | 09 |

---

# Phụ lục B — Vấn đề mở cần tác giả quyết định

Đây là các điểm mà việc sửa đòi hỏi quyết định nghiên cứu hoặc thiết kế, nên bản này chỉ đánh dấu, không tự chọn thay tác giả.

| Mã | Vấn đề | Vị trí | Gợi ý hướng xử lý |
| --- | --- | --- | --- |
| B-01 | URL SEC, trang thông cáo và URL CMU/SEI chưa được xác minh. | 1.5, 3.3 | Mở từng URL, ghi `access_date`, đổi `verification_status` sang `verified`. |
| B-02 | ~~Biến đầu vào và đầu ra trùng nhau.~~ Đã xử lý: loại AI-04, đầu vào chỉ là proxy CapEx/R&D. | 4.4, 4.6 | Không cần làm thêm. |
| B-03 | `normalization_method` chưa có; `composite_score` (DEC-01) và các bộ trọng số của SEN-01 chưa được định nghĩa, `Efficiency Score` (EFF-02) không có thành phần rủi ro. | 4.7, 4.8, 4.13 | Định nghĩa một điểm quyết định duy nhất với trọng số cho financial / ai_efficiency / market / risk và phương pháp chuẩn hóa. |
| B-04 | Chưa có phương pháp thống kê cho phân tích độ trễ; cỡ mẫu 16–20 quý với lag tới 4 làm giảm sức mạnh kiểm định. | 4.6, 2.5 | Chọn phương pháp (ví dụ tương quan chéo có trễ, hồi quy) và nêu giới hạn mẫu trong `limitations`. |
| B-05 | ~~Event study thiếu mô hình Expected Return.~~ Đã đặt mặc định market-adjusted return. | 4.9, 3.6 | Giữ mặc định; chỉ đổi sang market model nếu còn thời gian. |
| B-06 | Tên regime `Efficiency` trùng tên nhóm thước đo; chưa có ngưỡng phân loại. | 4.10 | Đổi tên regime và định nghĩa bảng quyết định/ngưỡng. |
| B-07 | ~~Chưa chỉ định nhà cung cấp và benchmark.~~ Đã chốt Yahoo Finance và S&P 500. | 3.4, 3.6, 7 | Có thể đổi, nhưng phải ghi lại phiên bản. |
| B-08 | Chưa có NFR về hiệu năng, bảo mật, khả dụng; danh sách người dùng và mức ưu tiên MoSCoW là đề xuất. | 1.6, 2.3, 5.3 | Xác nhận hoặc bổ sung theo yêu cầu môn học. |
| B-09 | Quy tắc căn chỉnh quý lịch (DAT-01) là đề xuất bổ sung. | 6.1 | Xác nhận quy tắc ghép quý. |
