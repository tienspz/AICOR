# Model card — aicor-pulse (pulse-1d2d9370)

- **Run:** `20261103T144352Z-9bc981`
- **As of:** 2026-07-29
- **Config version:** `aicor-analysis-v1`
- **Feature set:** `features-v1`
- **Target:** `E` · horizons [0, 1]
- **Samples:** 22
- **Artifact hash:** `19443d610b4bf62106ae5bb7f9b13cf7bfce9d693b957e1192320ea8d326bdc5`

## As-of policy
Mọi feature chỉ dùng dữ liệu có available_at <= as_of_date; giá trị target chỉ dùng để huấn luyện/đánh giá.

## Features
- `e_lag1`
- `e_lag2`
- `out_lag1`
- `in_lag1`
- `rd_intensity_lag1`
- `capex_intensity_lag1`
- `product_ma4q_lag1`
- `trends_ma4q_lag1`
- `is_msft`
- `target_quarter_num`

## Hyperparameters
```json
{
  "alpha_grid": [
    0.01,
    0.1,
    1.0,
    10.0
  ],
  "conformal_window": 8,
  "random_state": 42,
  "standardization": "train-only mean/std, median imputation"
}
```

## Backtest (h=0, pooled)
| Model | n | MAE | RMSE | Directional accuracy |
| --- | --- | --- | --- | --- |
| naive | 8 | 0.6561 | 0.8217 | 0.0 |
| ar1 | 8 | 0.6639 | 0.9639 | 0.625 |
| ridge | 8 | 1.0509 | 1.3818 | 0.625 |

## Quality gate (FCST-08)
**Passed:** False — primary_model_does_not_beat_naive

```json
[
  {
    "horizon": 0,
    "status": "fail",
    "model_mae": 1.0509,
    "naive_mae": 0.656137,
    "model_rmse": 1.381778,
    "naive_rmse": 0.821726,
    "n": 8
  },
  {
    "horizon": 1,
    "status": "fail",
    "model_mae": 1.041442,
    "naive_mae": 1.032192,
    "model_rmse": 1.233492,
    "naive_rmse": 1.253294,
    "n": 6
  }
]
```

## Interval method
split-conformal on chronological calibration block; normal fallback if <3 residuals · levels [0.8, 0.95]

## Limits
- N rất nhỏ: tối đa vài chục quan sát pooled sau khi z16Q đủ cửa sổ; kết quả nhạy với lựa chọn feature.
- R&D là proxy cho đầu tư AI, không phải chi tiêu AI được công bố riêng.
- Google Trends là chỉ số tương đối, phụ thuộc bộ từ khóa và địa lý đã chốt.
- Mô hình tuyến tính, không có deep learning (SPEC §5, FCST-05).
- Forecast không biết sự kiện sản phẩm tương lai; chủ yếu dựa trên momentum và seasonality.
- Driver attribution là yếu tố đóng góp trong mô hình, KHÔNG phải quan hệ nhân quả.
- Đây là thử nghiệm nghiên cứu, không phải khuyến nghị đầu tư.

_Experimental research output — không phải khuyến nghị đầu tư._
