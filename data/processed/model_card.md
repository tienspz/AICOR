# Model card — aicor-pulse (pulse-1d2d9370)

- **Run:** `20261104T001457Z-5f0e59`
- **As of:** 2026-10-29
- **Config version:** `aicor-analysis-v1`
- **Feature set:** `features-v1`
- **Target:** `E` · horizons [0, 1]
- **Samples:** 26
- **Artifact hash:** `ddddbe4242119c2f69c798377d36881f7cc9e378e2c03e23318fa0ab3d59f171`

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
| naive | 10 | 0.7228 | 0.9081 | 0.0 |
| ar1 | 10 | 0.6886 | 0.9509 | 0.7 |
| ridge | 10 | 0.6734 | 0.8931 | 0.7 |

## Quality gate (FCST-08)
**Passed:** True — ok

```json
[
  {
    "horizon": 0,
    "status": "pass",
    "model_mae": 0.673363,
    "naive_mae": 0.722783,
    "model_rmse": 0.893127,
    "naive_rmse": 0.908068,
    "n": 10
  },
  {
    "horizon": 1,
    "status": "pass",
    "model_mae": 0.853906,
    "naive_mae": 0.975146,
    "model_rmse": 1.10047,
    "naive_rmse": 1.195154,
    "n": 8
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
