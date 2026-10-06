# Đặc tả yêu cầu phần mềm (SRS): AICOR

**Phân tích hiệu suất đầu tư AI và kết quả của Microsoft, OpenAI và Anthropic theo quý từ 2022 đến nay**

**Mã hệ thống:** AICOR
**Phiên bản:** 5.1
**Ngày:** 2026-09-30
**Môn học:** Data Analysis for Business Environment (71DAEE10012)

Cấu trúc tài liệu theo đề cương SRS của khóa Foundations of Software Engineering, Carnegie Mellon University: Introduction, System Description, Functional Requirements, External Interface Requirements, Technical Requirements, Open Issues.

---

# 1. Introduction

## 1.1 Purpose

Tài liệu này mô tả yêu cầu của hệ thống AICOR, một web phân tích **hiệu suất đầu tư AI và kết quả của Microsoft, OpenAI và Anthropic theo từng quý từ Q1/2022 đến quý gần nhất có dữ liệu hợp lệ**.

Hệ thống thu thập dữ liệu đầu vào liên quan đến đầu tư AI và các chỉ số đầu ra, sau đó chuẩn hóa và tính toán điểm `E` để so sánh sự thay đổi tương đối giữa đầu vào và đầu ra của từng công ty theo thời gian.

Trong AICOR:

* `In` đại diện cho mức đầu vào/chi tiêu liên quan đến AI.
* `Out` đại diện cho kết quả đầu ra được tổng hợp từ hoạt động sản phẩm AI và mức độ quan tâm trên Google Trends.
* `E = Out - In` là điểm hiệu suất tương đối theo thời gian.

**Điểm E không phải ROI, lợi nhuận tài chính hoặc tỷ lệ hoàn vốn.**
E chỉ cho biết trong một quý, đầu ra có tăng nhanh hơn đầu vào hay không **so với mức lịch sử của chính công ty đó**.

Tất cả kết luận của hệ thống chỉ ở mức **tương quan và mô tả**, không khẳng định rằng đầu tư AI là nguyên nhân trực tiếp tạo ra kết quả đầu ra.

Người đọc dự kiến:

* Giảng viên môn học.
* Nhóm sinh viên phát triển hệ thống.
* Người dùng cuối được nêu tại mục 2.

---

## 1.2 Document conventions

* Yêu cầu chức năng đánh mã `FR-xx`.
* Yêu cầu phi chức năng đánh mã `NFR-xx`.
* Use case đánh mã `UC-x`.
* Giao diện ngoài đánh mã `IF-x`.
* Từ **“phải” (shall)** chỉ yêu cầu bắt buộc.
* Từ **“nên” (should)** chỉ yêu cầu mong muốn.
* Mức ưu tiên sử dụng `Must`, `Should`, `Could`.
* Ký hiệu quý: `2022-Q1`, `2022-Q2`, ...
* Phạm vi thời gian mặc định: **từ Q1/2022 đến quý gần nhất có dữ liệu hợp lệ**.
* Tiền tệ: USD.
* Chuẩn hóa chỉ số: z-score theo chuỗi thời gian của từng công ty.
* Các công ty được phân tích riêng theo lịch sử của chính công ty đó; không dùng E để khẳng định công ty nào có hiệu suất tuyệt đối cao hơn công ty khác.
* Tài liệu viết bằng tiếng Việt, giữ nguyên tên riêng và thuật ngữ tiếng Anh.

---

## 1.3 Project scope

### 1.3.1 Trong phạm vi

Hệ thống bao gồm:

* Thu thập dữ liệu theo quý từ **Q1/2022 đến quý gần nhất có dữ liệu hợp lệ**.
* Thu thập tự động:

  * Chi phí R&D của Microsoft.
  * Ước tính chi tiêu AI của OpenAI.
  * Ước tính chi tiêu AI của Anthropic.
  * Sản phẩm/tính năng AI được công bố.
  * Các mốc gọi vốn.
  * Google Trends.
  * Giá cổ phiếu Microsoft.
  * Các sự kiện quan hệ giữa ba công ty.
* Chuẩn hóa dữ liệu theo chuỗi thời gian của từng công ty.
* Tính:

  * `In`.
  * `Out`.
  * `E = Out - In`.
* Tính E theo từng quý cho từng công ty.
* Phân tích độ nhạy với ba bộ trọng số.
* Hiển thị đồ thị E theo quý.
* Hiển thị riêng đồ thị `In` và `Out`.
* Hiển thị timeline các sự kiện liên quan.
* Cung cấp công cụ chia tỷ lệ vốn mang tính **minh họa** dựa trên E.
* Lưu dữ liệu theo hình thức chỉ thêm, không xóa dữ liệu lịch sử.

### 1.3.2 Ngoài phạm vi

Hệ thống không bao gồm:

* Dự báo E hoặc dự báo giá cổ phiếu trong tương lai.
* Tính ROI hoặc lợi nhuận đầu tư tài chính thực tế.
* Khẳng định quan hệ nhân quả giữa đầu tư AI và kết quả.
* Khuyến nghị mua, bán hoặc đầu tư vào bất kỳ công ty nào.
* Khái quát hóa kết quả cho toàn bộ ngành AI.
* Khẳng định một công ty có hiệu suất đầu tư tuyệt đối cao hơn công ty khác dựa trên E.

Công cụ chia vốn chỉ nhằm **minh họa cách kết quả E có thể thay đổi khi người dùng thay đổi tỷ trọng**, không phải công cụ tư vấn đầu tư.

---

## 1.4 References

* Báo cáo 10-Q của Microsoft trên SEC EDGAR: https://www.sec.gov/edgar
* Google Trends: https://trends.google.com
* Blog chính thức của Microsoft.
* Blog/changelog chính thức của OpenAI.
* Blog/changelog chính thức của Anthropic.
* `yfinance`: thư viện Python truy cập dữ liệu giá.
* `pytrends`: thư viện Python truy cập Google Trends.
* Tài liệu GitHub Actions.
* Tài liệu GitHub Pages hoặc Vercel.
* Giáo trình requirements của khóa CMU 17-313.

---

# 2. System Description

## 2.1 Tổng quan hệ thống

AICOR gồm ba lớp chạy tuần tự:

### Lớp 1 — Collection

Các workflow GitHub Actions chạy theo lịch và gọi dữ liệu từ các nguồn bên ngoài.

Dữ liệu thô được ghi vào các file CSV trong repository theo hình thức **append-only**.

Các nguồn chính:

* SEC EDGAR.
* Yahoo Finance thông qua `yfinance`.
* Google Trends thông qua `pytrends`.
* Blog/changelog chính thức.
* Nguồn công khai dùng để xác định các mốc gọi vốn và ước tính chi tiêu.

### Lớp 2 — Computation

Script Python thực hiện:

1. Đọc dữ liệu thô.
2. Làm sạch dữ liệu.
3. Kiểm tra dữ liệu thiếu.
4. Gộp dữ liệu theo quý.
5. Tính các chỉ số đầu vào.
6. Tính các chỉ số đầu ra.
7. Chuẩn hóa z-score.
8. Tính `E = Out - In`.
9. Chạy phân tích độ nhạy.
10. Ghi kết quả vào SQLite.

### Lớp 3 — Display

Web React đọc dữ liệu đã được tính toán từ SQLite/JSON và manifest.

Web **không tự thực hiện lại phép tính E**.

---

## 2.2 Phạm vi dữ liệu theo thời gian

AICOR sử dụng dữ liệu:

> **Từ Q1/2022 đến quý gần nhất có dữ liệu hợp lệ tại thời điểm cập nhật hệ thống.**

Ví dụ:

```text
2022-Q1
2022-Q2
2022-Q3
...
2026-Q3
```

Nếu một quý chưa có đủ dữ liệu cần thiết, quý đó được đánh dấu thiếu dữ liệu và không được sử dụng trong các phép tính yêu cầu đầy đủ dữ liệu.

Do dữ liệu được cập nhật theo thời gian, số lượng quý trong hệ thống **không cố định**.

---

## 2.3 Nhịp cập nhật

### Nhịp nhanh

Mỗi **6 giờ**:

* Giá cổ phiếu Microsoft.
* Google Trends.

### Nhịp chậm

Mỗi **ngày một lần**:

* Sản phẩm/tính năng mới.
* Mốc gọi vốn.
* Ước tính chi tiêu AI.
* Sự kiện quan hệ.

### Microsoft 10-Q

Hệ thống kiểm tra filing mới trên SEC EDGAR và đồng bộ dữ liệu khi Microsoft phát hành 10-Q mới.

Dữ liệu có thể xuất hiện sau vài tuần kể từ khi kết thúc quý.

### Không có máy chủ chạy liên tục

AICOR sử dụng GitHub Actions để thực hiện các tác vụ định kỳ.

---

## 2.4 Actors

| Actor                          | Vai trò                                                        |
| ------------------------------ | -------------------------------------------------------------- |
| Nhà đầu tư quan tâm đến R&D    | Xem xu hướng E và thử các tỷ lệ phân bổ vốn mang tính minh họa |
| Đội R&D công ty khác           | Tham khảo xu hướng đầu tư và kết quả của các công ty           |
| Nhà báo công nghệ / giảng viên | Tham khảo kết quả và kiểm tra nguồn dữ liệu                    |
| GitHub Actions scheduler       | Kích hoạt pipeline thu thập và tính toán                       |
| API / nguồn dữ liệu bên ngoài  | Cung cấp dữ liệu cho hệ thống                                  |

Ba công ty không độc lập hoàn toàn với nhau. Microsoft có quan hệ đầu tư/hợp tác với OpenAI và có các mối quan hệ hợp tác, cạnh tranh với các công ty AI khác.

AICOR chỉ mã hóa những quan hệ có thông tin công khai và có nguồn xác minh được. Hệ thống không suy diễn động cơ phía sau các quan hệ này.

---

# 3. Functional Requirements

## 3.1 System features

Hệ thống gồm sáu nhóm tính năng:

1. Thu thập dữ liệu định kỳ.
2. Tính đầu vào và đầu ra.
3. Tính điểm hiệu suất tương đối E.
4. Phân tích độ nhạy và bối cảnh sự kiện.
5. Công cụ phân bổ vốn minh họa.
6. Hiển thị trạng thái hệ thống.

| Mã    | Yêu cầu                                                                                                                                                     | Ưu tiên |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| FR-01 | Hệ thống phải chạy nhịp nhanh mỗi 6 giờ để lấy giá cổ phiếu Microsoft và Google Trends                                                                      | Must    |
| FR-02 | Hệ thống phải chạy nhịp chậm mỗi ngày một lần để lấy sản phẩm ra mắt, mốc gọi vốn, ước tính chi tiêu và sự kiện quan hệ                                     | Must    |
| FR-03 | Hệ thống phải phát hiện 10-Q mới của Microsoft trên EDGAR và đồng bộ chi phí R&D                                                                            | Must    |
| FR-04 | Hệ thống phải tính `In`, `Out` và điểm `E = Out - In` theo công thức tại Phụ lục C cho từng công ty, từng quý                                               | Must    |
| FR-05 | Hệ thống phải chạy phân tích độ nhạy với ba bộ trọng số và chỉ đánh dấu kết luận là ổn định khi thứ tự tương đối giữa các công ty không thay đổi            | Must    |
| FR-06 | Hệ thống phải hiển thị đồ thị E theo quý cho từng công ty, kèm lớp bối cảnh đánh dấu mốc gọi vốn và sự kiện quan hệ                                         | Must    |
| FR-07 | Hệ thống phải hiển thị đồ thị `In` và `Out` riêng để người dùng theo dõi sự thay đổi của hai thành phần                                                     | Must    |
| FR-08 | Hệ thống nên hiển thị timeline sự kiện quan hệ phủ lên đồ thị E để người xem tự đối chiếu; hệ thống không được tự kết luận sự kiện nào gây ra thay đổi nào  | Should  |
| FR-09 | Hệ thống phải cung cấp ba thanh trượt chọn tỷ lệ phân bổ vốn, tổng tỷ lệ luôn bằng 100%                                                                     | Must    |
| FR-10 | Hệ thống phải tính điểm danh mục bằng tổng có trọng số của trung vị E trong 4 quý gần nhất và ghi rõ đây là công cụ minh họa, không phải khuyến nghị đầu tư | Must    |
| FR-11 | Hệ thống phải hiển thị trạng thái đồng bộ gần nhất và kết quả thành công/thất bại từ manifest                                                               | Must    |
| FR-12 | Hệ thống nên gọi API giá cổ phiếu mỗi phút khi trang đang mở và hiển thị độ trễ của nguồn dữ liệu                                                           | Should  |
| FR-13 | Hệ thống phải lưu dữ liệu theo hình thức chỉ thêm; sửa hồi tố phải ghi thành dòng mới kèm ngày hiệu lực, không xóa dòng cũ                                  | Must    |
| FR-14 | Web phải chỉ đọc dữ liệu đã tính từ SQLite/JSON và manifest, không tự tính toán lại E                                                                       | Must    |

---

# 3.2 Use Cases

## 3.2.1 Use case overview

Các actor người dùng:

* Nhà đầu tư.
* Đội R&D.
* Nhà báo/giảng viên.

có thể sử dụng:

* `UC-1`: Xem điểm hiệu suất theo quý.
* `UC-2`: Thử phân bổ vốn.
* `UC-3`: Kiểm tra trạng thái đồng bộ.

GitHub Actions scheduler thực hiện:

* `UC-4`: Đồng bộ dữ liệu định kỳ.

`UC-1`, `UC-2`, `UC-3` sử dụng dữ liệu đã được `UC-4` cập nhật.

---

# 3.2.2 UC-1: Xem điểm hiệu suất theo quý

| Trường            | Nội dung                                                                                         |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| Scope             | Hệ thống AICOR                                                                                   |
| Level             | User goal                                                                                        |
| Primary actor     | Nhà đầu tư quan tâm đến R&D                                                                      |
| Preconditions     | Nhịp chậm đã chạy ít nhất một lần thành công; dữ liệu quý cần xem tồn tại trong `fact_quarterly` |
| Success guarantee | Người xem thấy đồ thị E của ba công ty và lớp bối cảnh sự kiện                                   |

### Main success scenario

1. Người dùng mở trang.
2. Hệ thống tải dữ liệu đã tính từ SQLite/JSON.
3. Hệ thống vẽ E theo quý cho từng công ty.
4. Người dùng chọn một công ty hoặc xem cả ba.
5. Người dùng rê chuột lên một điểm dữ liệu.
6. Hệ thống hiển thị `In`, `Out`, `E` và trạng thái độ tin cậy của quý đó.

### Extensions

**4a. Quý có dữ liệu ước tính độ tin cậy thấp**

Hệ thống hiển thị cảnh báo độ tin cậy thấp.

Quý này không được sử dụng trong các phép so sánh yêu cầu dữ liệu đáng tin cậy.

**5a. Dữ liệu chưa có**

Hệ thống hiển thị thông báo về thời điểm dữ liệu khả dụng gần nhất.

### Special requirements

* Thời gian tải theo `NFR-01`.
* Cách diễn đạt kết quả phải tuân thủ giới hạn tại Phụ lục C.
* Không sử dụng E để khẳng định ROI hoặc quan hệ nhân quả.

**Frequency:** Hàng ngày.

---

# 3.2.3 UC-2: Thử phân bổ vốn đầu tư

| Trường            | Nội dung                                                                     |
| ----------------- | ---------------------------------------------------------------------------- |
| Scope             | Hệ thống AICOR                                                               |
| Level             | User goal                                                                    |
| Primary actor     | Người dùng                                                                   |
| Preconditions     | UC-1 hiển thị được dữ liệu                                                   |
| Success guarantee | Điểm danh mục cập nhật khi thanh trượt thay đổi và tổng tỷ lệ luôn bằng 100% |

### Main success scenario

1. Người dùng điều chỉnh ba thanh trượt.
2. Hệ thống đảm bảo tổng tỷ lệ bằng 100%.
3. Hệ thống tính điểm danh mục theo FR-10.
4. Người dùng thay đổi tỷ trọng để quan sát sự thay đổi của điểm danh mục.

### Extensions

**3a. Công ty thiếu dữ liệu**

Nếu công ty không có đủ dữ liệu cần thiết trong 4 quý gần nhất:

* Hệ thống hiển thị cảnh báo.
* Không sử dụng dữ liệu thiếu để tạo kết quả giả.
* Thanh trượt có thể bị vô hiệu hóa tùy tình trạng dữ liệu.

### Special requirements

Nhãn:

> **“Công cụ minh họa, không phải khuyến nghị đầu tư.”**

phải luôn hiển thị cạnh kết quả.

**Frequency:** Hàng ngày.

---

# 3.2.4 UC-3: Kiểm tra trạng thái đồng bộ

| Trường            | Nội dung                                                              |
| ----------------- | --------------------------------------------------------------------- |
| Scope             | Hệ thống AICOR                                                        |
| Level             | User goal                                                             |
| Primary actor     | Nhà báo công nghệ, giảng viên                                         |
| Preconditions     | Tệp manifest tồn tại                                                  |
| Success guarantee | Người xem thấy thời điểm đồng bộ gần nhất và trạng thái của từng nhịp |

### Main success scenario

1. Người dùng mở trang.
2. Người dùng xem dòng trạng thái ở chân trang.
3. Hệ thống hiển thị:

   * Thời điểm đồng bộ gần nhất.
   * Trạng thái nhịp nhanh.
   * Trạng thái nhịp chậm.
   * Trạng thái EDGAR.

### Extensions

Nếu lần chạy gần nhất thất bại:

* Hiển thị cảnh báo.
* Hiển thị mã lỗi từ `sync_log`.
* Giữ nguyên dữ liệu thành công gần nhất.
* Không làm hỏng các chức năng hiển thị khác.

**Frequency:** Mỗi lần mở trang.

---

# 3.2.5 UC-4: Đồng bộ dữ liệu định kỳ

| Trường            | Nội dung                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------- |
| Scope             | Hệ thống AICOR                                                                              |
| Level             | Subprocess                                                                                  |
| Primary actor     | GitHub Actions scheduler                                                                    |
| Preconditions     | Workflow được lập lịch; repository khả dụng; API key được lưu trong GitHub Secrets          |
| Success guarantee | Dữ liệu mới được ghi vào CSV theo hình thức append-only; manifest và sync_log được cập nhật |

### Main success scenario

1. Scheduler kích hoạt workflow.
2. Hệ thống gọi API nguồn.
3. Hệ thống làm sạch dữ liệu.
4. Hệ thống kiểm tra dữ liệu bắt buộc.
5. Hệ thống ghi dữ liệu mới vào CSV.
6. Ở nhịp chậm, hệ thống gộp dữ liệu theo quý.
7. Hệ thống tính `In`, `Out`, `E`.
8. Hệ thống cập nhật SQLite/JSON.
9. Hệ thống cập nhật manifest.
10. Hệ thống ghi trạng thái thành công vào `sync_log`.

### Extensions

**2a. API lỗi hoặc vượt giới hạn tốc độ**

* Ghi `sync_log` với trạng thái `failed`.
* Không ghi dữ liệu rỗng.
* Giữ nguyên dữ liệu thành công trước đó.

**3a. Dữ liệu thiếu trường bắt buộc**

* Không đưa dòng dữ liệu lỗi vào kho chính.
* Ghi cảnh báo vào `sync_log`.

### Special requirements

Thời gian chạy một workflow không vượt quá giới hạn miễn phí của GitHub Actions.

**Frequency:**

* Nhịp nhanh: 6 giờ.
* Nhịp chậm: 1 ngày.

---

# 3.3 Entity Relationship Diagram

| Thực thể                 | Liên kết                                                   |
| ------------------------ | ---------------------------------------------------------- |
| `dim_company` (1)        | Có nhiều `fact_quarterly`, `event_launch`, `event_funding` |
| `fact_quarterly` (n)     | Thuộc 1 `dim_company`                                      |
| `event_launch` (n)       | Thuộc 1 `dim_company`                                      |
| `event_funding` (n)      | Thuộc 1 `dim_company`                                      |
| `event_relationship` (n) | Liên quan 2 đến 3 `dim_company`                            |
| `sync_log` (n)           | Độc lập, ghi nhật ký vận hành                              |

---

# 3.4 Data Dictionary

## 3.4.1 dim_company

| Trường       | Kiểu                  | Mô tả                              |
| ------------ | --------------------- | ---------------------------------- |
| `company_id` | Số nguyên, khóa chính | Định danh công ty                  |
| `name`       | Chuỗi                 | Microsoft, OpenAI, Anthropic       |
| `ticker`     | Chuỗi, có thể rỗng    | MSFT hoặc rỗng với công ty tư nhân |

---

## 3.4.2 fact_quarterly

| Trường           | Kiểu                      | Mô tả                                              |
| ---------------- | ------------------------- | -------------------------------------------------- |
| `company_id`     | Số nguyên, khóa ngoại     | Công ty                                            |
| `quarter`        | Chuỗi `YYYY-Qn`           | Quý                                                |
| `rnd_spend`      | Số thực, USD, có thể rỗng | Chi phí R&D của Microsoft                          |
| `ai_spend_est`   | Số thực, USD, có thể rỗng | Ước tính chi tiêu AI của OpenAI/Anthropic          |
| `est_confidence` | `high`, `medium`, `low`   | Độ tin cậy của ước tính                            |
| `trends_qavg`    | Số thực 0–100             | Google Trends trung bình quý                       |
| `product_score`  | Số thực                   | Điểm sản phẩm sau tính trọng số và trung bình động |
| `out_score`      | Số thực                   | Đầu ra tổng hợp sau chuẩn hóa                      |
| `in_score`       | Số thực                   | Đầu vào sau chuẩn hóa                              |
| `e_score`        | Số thực                   | Điểm `E = Out - In`                                |
| `valid_from`     | Ngày                      | Ngày hiệu lực của dòng dữ liệu                     |

---

## 3.4.3 event_launch

| Trường         | Kiểu                  | Mô tả               |
| -------------- | --------------------- | ------------------- |
| `company_id`   | Số nguyên, khóa ngoại | Công ty             |
| `launch_date`  | Ngày                  | Ngày công bố        |
| `product_name` | Chuỗi                 | Tên sản phẩm        |
| `category`     | Chuỗi: A, B, C        | Nhóm theo Phụ lục A |
| `source_url`   | Chuỗi                 | Nguồn chính thức    |
| `coder`        | Chuỗi                 | Người mã hóa        |

---

## 3.4.4 event_funding

| Trường         | Kiểu                      | Mô tả            |
| -------------- | ------------------------- | ---------------- |
| `company_id`   | Số nguyên, khóa ngoại     | Công ty          |
| `funding_date` | Ngày                      | Ngày công bố     |
| `amount`       | Số thực, USD              | Số tiền gọi được |
| `valuation`    | Số thực, USD, có thể rỗng | Định giá         |
| `source_url`   | Chuỗi                     | Nguồn            |

---

## 3.4.5 event_relationship

| Trường       | Kiểu  | Mô tả                                       |
| ------------ | ----- | ------------------------------------------- |
| `event_date` | Ngày  | Ngày sự kiện                                |
| `parties`    | Chuỗi | Các bên, cách nhau bằng dấu phẩy            |
| `rel_type`   | Chuỗi | `invest`, `partner`, `compete`, `statement` |
| `quote`      | Chuỗi | Trích dẫn nguyên văn                        |
| `source_url` | Chuỗi | Nguồn                                       |

---

## 3.4.6 sync_log

| Trường       | Kiểu                    | Mô tả             |
| ------------ | ----------------------- | ----------------- |
| `run_at`     | Ngày giờ UTC            | Thời điểm chạy    |
| `rhythm`     | `fast`, `slow`, `edgar` | Nhịp chạy         |
| `status`     | `success`, `failed`     | Kết quả           |
| `rows_added` | Số nguyên               | Số dòng thêm mới  |
| `error`      | Chuỗi, có thể rỗng      | Mã lỗi hoặc mô tả |

---

# 4. External Interface Requirements

| Mã   | Giao diện                    | Yêu cầu                                                                                  |
| ---- | ---------------------------- | ---------------------------------------------------------------------------------------- |
| IF-1 | SEC EDGAR API                | Lấy dữ liệu 10-Q của Microsoft, phát hiện filing mới và tuân thủ giới hạn tốc độ của SEC |
| IF-2 | Yahoo Finance qua `yfinance` | Lấy giá MSFT; dữ liệu có thể trễ khoảng 15 phút và phải hiển thị nhãn độ trễ             |
| IF-3 | Google Trends qua `pytrends` | Lấy dữ liệu Trends cho từng công ty/chủ đề cố định và tổng hợp theo quý                  |
| IF-4 | Blog/changelog chính thức    | Thu thập sản phẩm/tính năng và ngày công bố                                              |
| IF-5 | GitHub Actions               | Lập lịch workflow và lưu API key trong Secrets                                           |
| IF-6 | GitHub Pages hoặc Vercel     | Host web tĩnh                                                                            |
| IF-7 | Trình duyệt người dùng       | Đọc dữ liệu JSON/SQLite đã xử lý và manifest; gọi API giá khi trang mở                   |

### Xử lý lỗi chung

Mọi lần gọi API thất bại phải:

1. Ghi lỗi vào `sync_log`.
2. Không ghi dữ liệu rỗng vào kho.
3. Giữ nguyên dữ liệu thành công gần nhất.
4. Cập nhật trạng thái cảnh báo trên web nếu cần.

---

# 5. Technical Requirements — Non-functional Requirements

| Mã     | Nhóm                  | Yêu cầu                                                                                                                                         |
| ------ | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| NFR-01 | Performance           | Trang tải lần đầu không quá 3 giây trên kết nối 4G; widget giá hiển thị dữ liệu mới trong tối đa 2 giây sau khi nhận dữ liệu                    |
| NFR-02 | Scalability           | Lượt xem được phục vụ bởi static hosting; thời gian chạy workflow không vượt hạn mức miễn phí của GitHub Actions                                |
| NFR-03 | Security              | Dữ liệu công khai, chỉ đọc, không lưu thông tin cá nhân; API key phải được lưu trong GitHub Secrets                                             |
| NFR-04 | Maintainability       | Phép tính được đặt trong script Python có phiên bản trong repository; rubric và công thức nằm trong SRS; dữ liệu thô cho phép tái lập phép tính |
| NFR-05 | Usability             | Một trang chính, ba chế độ xem, nhãn tiếng Việt; thanh trượt phân bổ vốn thao tác bằng chuột                                                    |
| NFR-06 | Multi-lingual support | Giao diện tiếng Việt; tên riêng và thuật ngữ chuyên môn giữ nguyên tiếng Anh khi cần                                                            |
| NFR-07 | Auditing and logging  | Mỗi lần chạy ghi `sync_log`; manifest ghi thời gian và trạng thái; người mã hóa được ghi trong dữ liệu sự kiện                                  |
| NFR-08 | Availability          | Lỗi pipeline không làm hỏng web; web vẫn hiển thị dữ liệu thành công gần nhất                                                                   |
| NFR-09 | Reliability           | Quý thiếu dữ liệu cần thiết hoặc có độ tin cậy thấp phải được đánh dấu; z-score phải kiểm tra trường hợp phương sai bằng 0 trước khi chia       |

---

# 6. Open Issues

1. **Ước tính chi tiêu AI của OpenAI và Anthropic** không phải số liệu tài chính công khai đầy đủ và có thể không có cho mọi quý từ 2022 đến nay.

2. **Google Trends** là chỉ số tương đối và có nhiễu. Kết quả có thể thay đổi theo cách lựa chọn từ khóa và thời điểm truy vấn.

3. **Số lượng quan sát phụ thuộc thời điểm cập nhật.** Phạm vi bắt đầu từ Q1/2022 và kéo dài đến quý gần nhất có dữ liệu hợp lệ, do đó số quý không cố định.

4. **Mã hóa sản phẩm và quan hệ** có thành phần thủ công. Cần kiểm tra chéo trên một mẫu dữ liệu để giảm sai lệch giữa người mã hóa.

5. **Trọng số 0.6/0.4** trong `Out` là giả định khởi đầu. Phân tích độ nhạy tại FR-05 được dùng để kiểm tra mức độ ổn định của kết quả khi thay đổi trọng số.

6. **Microsoft R&D không chỉ dành riêng cho AI**, do đó `In` của Microsoft là đại diện cho đầu vào R&D rộng hơn, không phải toàn bộ chi tiêu AI.

7. **Dự báo** chưa thuộc phạm vi hiện tại và có thể được xem xét sau khi tích lũy đủ dữ liệu.

---

# Phụ lục A. Rubric đếm sản phẩm ra mắt

Chỉ đếm sản phẩm/tính năng đáp ứng đồng thời:

* Có tên gọi cụ thể.
* Có thông tin công bố trên blog hoặc changelog chính thức.
* Có ngày công bố xác định được.

Mỗi mục được gán đúng một nhóm:

### Nhóm A

Model chính mới có:

* Báo cáo kỹ thuật riêng; hoặc
* Bài giới thiệu riêng.

Trọng số:

```text
3 điểm
```

### Nhóm B

Bao gồm:

* Model biến thể.
* API lớn.
* Bản mở rộng đáng kể.

Trọng số:

```text
2 điểm
```

### Nhóm C

Bao gồm:

* Tính năng sản phẩm.
* Tích hợp.
* Cập nhật nhỏ.

Trọng số:

```text
1 điểm
```

Nếu cùng một sản phẩm xuất hiện trên nhiều kênh chính thức, chỉ tính một lần.

Điểm sản phẩm của quý:

```text
Product Score
= 3 × số mục nhóm A
+ 2 × số mục nhóm B
+ 1 × số mục nhóm C
```

Sau đó tính **trung bình động 4 quý** trước khi đưa vào `Out`.

Nếu chưa đủ dữ liệu cho cửa sổ 4 quý, hệ thống đánh dấu dữ liệu chưa đủ và không tạo kết quả giả.

---

# Phụ lục B. Rubric mã hóa quan hệ ba bên

Mỗi sự kiện gồm:

* Ngày.
* Các bên liên quan.
* Loại quan hệ.
* Trích dẫn nguyên văn nếu có.
* Nguồn.

Bốn loại quan hệ:

| Loại        | Ý nghĩa            |
| ----------- | ------------------ |
| `invest`    | Đầu tư             |
| `partner`   | Hợp tác            |
| `compete`   | Cạnh tranh         |
| `statement` | Phát ngôn có nguồn |

Một sự kiện có thể mang nhiều loại.

Ví dụ:

```text
partner + compete
```

có thể được sử dụng nếu hai công ty vừa có quan hệ hợp tác vừa cạnh tranh ở một sản phẩm/thị trường cụ thể.

Không suy diễn động cơ.

Chỉ mã hóa những gì có thể xác minh từ nguồn công khai.

---

# Phụ lục C. Công thức điểm hiệu suất

## C.1. Ý nghĩa chung

AICOR sử dụng ba đại lượng chính:

```text
In  = Đầu vào / mức đầu tư
Out = Kết quả đầu ra
E   = Out - In
```

Điểm `E` được dùng để mô tả **mức độ thay đổi tương đối giữa đầu vào và đầu ra theo thời gian**.

E không phải:

* ROI.
* Lợi nhuận.
* Tỷ lệ hoàn vốn.
* Hiệu quả tài chính tuyệt đối.
* Bằng chứng về quan hệ nhân quả.

---

## C.2. Chuẩn hóa dữ liệu

Mọi chỉ số được chuẩn hóa bằng z-score theo chuỗi thời gian của **chính công ty đó**.

Công thức:

```text
z(x) = (x - mean(x)) / standard_deviation(x)
```

Việc chuẩn hóa theo từng công ty giúp AICOR tập trung vào câu hỏi:

> Trong quý này, chỉ số của công ty đang cao hay thấp hơn mức lịch sử của chính công ty đó?

Không dùng E để so sánh trực tiếp quy mô tuyệt đối giữa Microsoft, OpenAI và Anthropic.

---

## C.3. Đầu ra — Out

Đầu ra được tạo từ hai thành phần:

1. Hoạt động sản phẩm AI.
2. Google Trends.

Công thức:

```text
Out(c, q)
=
0.6 × z(Product Moving Average 4Q)
+
0.4 × z(Google Trends Moving Average 4Q)
```

Trong đó:

```text
Product Moving Average 4Q
```

là trung bình động của điểm sản phẩm trong 4 quý.

`Google Trends Moving Average 4Q` là trung bình động Google Trends trong 4 quý.

---

## C.4. Đầu vào — In

### Microsoft

```text
In(Microsoft, q)
=
z(Quarterly R&D Cost)
```

Chi phí R&D được lấy từ báo cáo tài chính/10-Q của Microsoft.

Lưu ý:

> Chi phí R&D của Microsoft không chỉ dành riêng cho AI.

Vì vậy `In` của Microsoft là đại diện cho **đầu vào R&D**, không phải số tiền AI thuần túy.

### OpenAI và Anthropic

```text
In(c, q)
=
z(Estimated AI Spending)
```

Chi tiêu AI của OpenAI và Anthropic là số liệu **ước tính** từ các nguồn công khai.

Mỗi quý phải có trường:

```text
est_confidence
```

với một trong ba mức:

```text
high
medium
low
```

Quý có độ tin cậy `low` không được dùng cho kết luận chính.

---

# C.5. Điểm hiệu suất E

Công thức chính:

```text
E(c, q) = Out(c, q) - In(c, q)
```

### E > 0

Có nghĩa:

> Trong quý đó, **đầu ra tăng tương đối nhanh hơn đầu vào so với mức lịch sử của chính công ty**.

### E < 0

Có nghĩa:

> Trong quý đó, **đầu vào tăng tương đối nhanh hơn đầu ra so với mức lịch sử của chính công ty**.

### E ≈ 0

Có nghĩa:

> Mức thay đổi tương đối của đầu vào và đầu ra gần nhau.

---

## C.6. Ví dụ diễn giải

Giả sử:

```text
In  = 0.8
Out = 1.3
```

Khi đó:

```text
E = 1.3 - 0.8
  = +0.5
```

Diễn giải:

> Quý này, đầu ra tăng tương đối nhanh hơn đầu vào so với mức lịch sử của công ty.

**Không được diễn giải thành:**

```text
Đầu tư 1 USD tạo ra 0.5 USD kết quả.
```

hoặc:

```text
ROI = 50%.
```

---

# C.7. Điểm danh mục

Công cụ phân bổ vốn sử dụng:

```text
Portfolio Score
=
Σ(w_c × Median(E_c, recent 4 quarters))
```

Trong đó:

```text
w_MSFT + w_OpenAI + w_Anthropic = 1
```

Người dùng có thể thay đổi ba trọng số thông qua thanh trượt.

Điểm danh mục chỉ có mục đích **minh họa sự thay đổi của kết quả E khi thay đổi tỷ trọng**.

Nó không phải:

* dự báo lợi nhuận;
* khuyến nghị đầu tư;
* dự báo giá cổ phiếu;
* cam kết kết quả đầu tư.

---

# C.8. Phân tích độ nhạy

AICOR chạy lại phép tính `Out` với ba bộ trọng số:

### Bộ 1 — Mặc định

```text
Product = 0.6
Trends  = 0.4
```

### Bộ 2

```text
Product = 0.5
Trends  = 0.5
```

### Bộ 3

```text
Product = 0.7
Trends  = 0.3
```

Mục đích là kiểm tra xem kết quả có thay đổi đáng kể khi thay đổi giả định về trọng số hay không.

Nếu thứ tự tương đối giữa ba công ty thay đổi giữa các bộ trọng số, hệ thống phải đánh dấu kết quả là **nhạy với trọng số**.

Nếu thứ tự không thay đổi, kết quả được đánh dấu là **ổn định với ba bộ trọng số đã kiểm tra**.

Phân tích độ nhạy chỉ phản ánh độ ổn định của phép đo E, không chứng minh quan hệ nhân quả.

---

# C.9. Quy tắc diễn đạt kết quả

Hệ thống và báo cáo nên sử dụng cách diễn đạt:

> **“Trong quý này, đầu ra tăng nhanh hơn đầu vào so với mức lịch sử của công ty.”**

hoặc:

> **“Trong quý này, đầu vào tăng nhanh hơn đầu ra so với mức lịch sử của công ty.”**

Không sử dụng các câu:

> “Công ty A đầu tư hiệu quả nhất.”

> “Công ty A có ROI cao nhất.”

> “Đầu tư thêm 1 USD tạo ra X USD kết quả.”

> “Đầu tư AI là nguyên nhân làm kết quả tăng.”

Các câu trên vượt quá ý nghĩa mà chỉ số E có thể chứng minh.

---

# Phụ lục D. Giới hạn phân tích

AICOR có các giới hạn chính:

### D.1. Không chứng minh quan hệ nhân quả

E chỉ mô tả sự thay đổi tương đối giữa đầu vào và đầu ra.

Một giá trị E dương không chứng minh rằng đầu tư AI là nguyên nhân trực tiếp làm đầu ra tăng.

---

### D.2. Microsoft R&D không chỉ dành cho AI

Dữ liệu R&D của Microsoft bao gồm nhiều hoạt động nghiên cứu và phát triển khác nhau.

Do đó:

```text
Microsoft In ≠ Chi tiêu AI thuần túy
```

mà là đại diện cho đầu vào R&D của công ty.

---

### D.3. OpenAI và Anthropic là công ty tư nhân

Dữ liệu chi tiêu AI không được công bố đầy đủ như báo cáo tài chính của công ty đại chúng.

Do đó các giá trị:

```text
ai_spend_est
```

có thể có sai số.

Hệ thống phải lưu mức độ tin cậy của từng ước tính.

---

### D.4. Dữ liệu sản phẩm có thể có thiên lệch

Việc đếm sản phẩm dựa trên blog/changelog chính thức của công ty.

Do đó dữ liệu có thể phản ánh cách công ty công bố sản phẩm và không nhất thiết phản ánh toàn bộ hoạt động phát triển AI nội bộ.

---

### D.5. Google Trends là chỉ số tương đối

Google Trends không phải số lượng người dùng thực tế hay doanh thu.

Kết quả có thể bị ảnh hưởng bởi:

* từ khóa;
* thời điểm;
* xu hướng truyền thông;
* sự kiện bất thường.

---

### D.6. Số lượng quan sát

Phạm vi bắt đầu từ:

```text
Q1/2022
```

và kết thúc tại:

```text
quý gần nhất có dữ liệu hợp lệ
```

Do đó số lượng quý thay đổi theo thời điểm hệ thống được cập nhật.

Số lượng quan sát vẫn tương đối nhỏ đối với các phân tích thống kê phức tạp.

---

### D.7. Ba công ty không đại diện cho toàn ngành

AICOR chỉ phân tích:

```text
Microsoft
OpenAI
Anthropic
```

Do đó kết quả không được dùng để khái quát cho toàn bộ ngành AI.

---

### D.8. E không phải thước đo hiệu suất tuyệt đối

E chỉ là một **chỉ số hiệu suất tương đối theo thời gian**.

Có thể hiểu:

```text
E > 0
→ Output tăng tương đối nhanh hơn Input

E < 0
→ Input tăng tương đối nhanh hơn Output
```

Không được hiểu:

```text
E = ROI
E = lợi nhuận
E = hiệu suất tài chính
```

---

# Phụ lục E. Tóm tắt logic xử lý dữ liệu

Pipeline tổng quát:

```text
Nguồn dữ liệu
     ↓
Thu thập tự động
     ↓
Raw CSV
     ↓
Làm sạch + kiểm tra
     ↓
Gộp theo quý
     ↓
Tính Product Score
     ↓
Moving Average 4Q
     ↓
Chuẩn hóa z-score
     ↓
       ┌───────────────┐
       │               │
       ↓               ↓
      In              Out
       │               │
       └───────┬───────┘
               ↓
          E = Out - In
               ↓
      Phân tích độ nhạy
               ↓
          SQLite / JSON
               ↓
          React Web App
```

---

# Phụ lục F. Ý nghĩa của AICOR

AICOR trả lời câu hỏi:

> **“Theo từng quý, mức đầu vào liên quan đến AI của mỗi công ty thay đổi như thế nào so với kết quả đầu ra, và mối quan hệ tương đối đó có ổn định khi thay đổi cách tính trọng số hay không?”**

AICOR **không trả lời**:

> “Công ty nào đầu tư AI sinh lời nhất?”

và cũng không trả lời:

> “Đầu tư AI bao nhiêu thì chắc chắn tạo ra bao nhiêu kết quả?”

Mục tiêu của hệ thống là cung cấp một cách **định lượng, trực quan và có thể kiểm tra lại** để theo dõi sự thay đổi của đầu vào và đầu ra AI theo thời gian.
