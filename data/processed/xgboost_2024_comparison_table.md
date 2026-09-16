# 2024 XGBoost Actual vs Predicted Freight Rate

| Month | Actual Freight ($/day) | XGBoost Prediction ($/day) | Difference ($/day) | Difference (%) | Prediction Lower? | Absolute Error ($/day) |
|---|---:|---:|---:|---:|:---:|---:|
| Jan 2024 | 12,058.00 | 13,243.16 | +1,185.16 | +9.83% | NO | 1,185.16 |
| Feb 2024 | 3,000.00 | 12,100.93 | +9,100.93 | +303.36% | NO | 9,100.93 |
| Mar 2024 | 12,454.00 | 12,879.67 | +425.67 | +3.42% | NO | 425.67 |
| Apr 2024 | 14,640.00 | 14,237.65 | -402.35 | -2.75% | YES | 402.35 |
| May 2024 | 12,409.00 | 12,789.23 | +380.23 | +3.06% | NO | 380.23 |
| Jun 2024 | 14,332.00 | 12,833.36 | -1,498.64 | -10.46% | YES | 1,498.64 |
| Jul 2024 | 13,091.00 | 11,191.15 | -1,899.85 | -14.51% | YES | 1,899.85 |
| Aug 2024 | 11,215.00 | 12,001.77 | +786.77 | +7.02% | NO | 786.77 |
| Sep 2024 | 11,862.00 | 9,193.51 | -2,668.49 | -22.50% | YES | 2,668.49 |
| Oct 2024 | 12,633.00 | 11,088.41 | -1,544.59 | -12.23% | YES | 1,544.59 |
| Nov 2024 | 12,780.00 | 9,693.38 | -3,086.62 | -24.15% | YES | 3,086.62 |
| Dec 2024 | 8,781.00 | 11,215.50 | +2,434.50 | +27.72% | NO | 2,434.50 |

## Summary

| Metric | Value |
|---|---:|
| Months evaluated | 12 |
| Prediction lower than actual | 6 / 12 |
| Prediction higher than actual | 6 / 12 |
| Average actual freight | $11,604.58/day |
| Average XGBoost prediction | $11,872.31/day |
| Average difference | +$267.73/day |
| MAE | $2,117.82/day |
| RMSE | $3,111.19/day |
| MAPE | 36.75% |