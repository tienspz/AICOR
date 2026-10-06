# AICOR: AI Investment and Outcome Performance Pipeline

**Phân tích hiệu suất đầu tư AI và kết quả của Microsoft, OpenAI và Anthropic theo quý từ 2022 đến nay.**  
Tuân thủ đặc tả yêu cầu phần mềm CMU SRS v5.1 (Khóa Foundations of Software Engineering, Carnegie Mellon University).

---

## 🚀 Tính năng Cốt lõi

1. **Thu thập Dữ liệu Đa nguồn (Lớp 1 - Collection)**:
   - SEC EDGAR 10-Q / 10-K (Chi phí R&D Microsoft).
   - Yahoo Finance (Giá cổ phiếu MSFT).
   - Google Trends (Chỉ số quan tâm Microsoft AI, OpenAI, Anthropic).
   - Blog/Changelog chính thức (Sản phẩm ra mắt theo rubric Nhóm A: 3đ, B: 2đ, C: 1đ).
   - Mốc gọi vốn & Sự kiện quan hệ ba bên (`invest`, `partner`, `compete`, `statement`).
   - Ước tính chi tiêu AI (OpenAI & Anthropic kèm cờ độ tin cậy `high`/`medium`/`low`).

2. **Cơ chế Chống Ban IP & Rate Limiting**:
   - Token-bucket throttle (SEC EDGAR $\le$ 10 req/s, Google Trends giãn cách 3–6s + random jitter).
   - Exponential Backoff tự động khi gặp HTTP 429 Too Many Requests.

3. **Tính toán Chỉ số & Phân tích Độ nhạy (Lớp 2 - Computation)**:
   - Chuẩn hóa Z-score **riêng trong chuỗi lịch sử của từng công ty** (có bảo vệ chống chia cho 0).
   - Tính trung bình động 4 quý (Rolling 4Q MA) cho Product Score và Google Trends.
   - Tính điểm hiệu suất: $E = Out - In$ ($E > 0$: Output tăng nhanh hơn Input so với lịch sử của công ty).
   - Phân tích độ nhạy với 3 bộ trọng số (0.6/0.4, 0.5/0.5, 0.7/0.3).

4. **Lưu trữ CSV 3 Tầng**:
   - `data/raw/*.csv`: Dữ liệu thô append-only, khử trùng lặp qua natural keys.
   - `data/cleaned/*.csv`: Dữ liệu sạch đã chuẩn hóa và phân loại rubric.
   - `data/processed/*.csv`: Bảng dữ liệu quý tổng hợp (`fact_quarterly.csv`), phân tích độ nhạy (`sensitivity_analysis.csv`), và nhật ký vận hành (`sync_log.csv`).

---

## 🛠️ Cài đặt & Sử dụng

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2. Chạy Pipeline bằng CLI
```bash
# Khởi tạo dữ liệu mẫu ban đầu từ 2022-Q1 đến nay:
python run_pipeline.py --mode seed

# Chạy toàn bộ pipeline (Crawl -> Làm sạch -> Tính toán xuất CSV):
python run_pipeline.py --mode full

# Chỉ làm sạch dữ liệu từ raw sang cleaned:
python run_pipeline.py --mode clean

# Chỉ tính toán lại các chỉ số In, Out, E từ cleaned sang processed:
python run_pipeline.py --mode compute
```

### 3. Chạy Kiểm thử (TDD)
```bash
python -m pytest tests/
```

---

## ☁️ Tự động hóa 24/7 với GitHub Actions

Hệ thống được lập lịch chạy tự động trên GitHub Cloud:
- **Nhịp nhanh (Mỗi 6 tiếng)**: Cập nhật giá cổ phiếu và Google Trends (`fast_rhythm.yml`).
- **Nhịp chậm (Hàng ngày lúc 02:00 UTC)**: Chạy full pipeline, làm sạch và cập nhật lại `fact_quarterly.csv` (`slow_rhythm.yml`).
- Tự động `git commit` và `git push` các file CSV mới vào kho lưu trữ với `[skip ci]`.
