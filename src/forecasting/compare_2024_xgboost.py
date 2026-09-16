import pandas as pd
import numpy as np
from pathlib import Path

# ---------------------------------------------------------
# 2024 XGBoost Actual vs Predicted Freight Rate Comparison
# ---------------------------------------------------------

data = [
    ["2024-01-01", 12058, 13243.160],
    ["2024-02-01", 3000, 12100.929],
    ["2024-03-01", 12454, 12879.672],
    ["2024-04-01", 14640, 14237.645],
    ["2024-05-01", 12409, 12789.230],
    ["2024-06-01", 14332, 12833.359],
    ["2024-07-01", 13091, 11191.146],
    ["2024-08-01", 11215, 12001.768],
    ["2024-09-01", 11862, 9193.514],
    ["2024-10-01", 12633, 11088.411],
    ["2024-11-01", 12780, 9693.375],
    ["2024-12-01", 8781, 11215.496],
]

df = pd.DataFrame(
    data,
    columns=["Date", "Actual Freight", "XGBoost Prediction"]
)

# Difference: Prediction - Actual
df["Difference"] = df["XGBoost Prediction"] - df["Actual Freight"]

# Percentage difference
df["Difference (%)"] = (
    df["Difference"] / df["Actual Freight"] * 100
)

# Whether model predicted a lower freight rate
df["Prediction Lower?"] = np.where(
    df["XGBoost Prediction"] < df["Actual Freight"],
    "YES",
    "NO"
)

# Absolute error
df["Absolute Error"] = abs(df["Difference"])

# ---------------------------------------------------------
# Display table
# ---------------------------------------------------------

print("\n" + "=" * 100)
print("2024 XGBOOST ACTUAL VS PREDICTED FREIGHT RATE")
print("=" * 100)

display_df = df.copy()

display_df["Actual Freight"] = display_df["Actual Freight"].map(
    lambda x: f"{x:,.2f}"
)
display_df["XGBoost Prediction"] = display_df["XGBoost Prediction"].map(
    lambda x: f"{x:,.2f}"
)
display_df["Difference"] = display_df["Difference"].map(
    lambda x: f"{x:+,.2f}"
)
display_df["Difference (%)"] = display_df["Difference (%)"].map(
    lambda x: f"{x:+.2f}%"
)
display_df["Absolute Error"] = display_df["Absolute Error"].map(
    lambda x: f"{x:,.2f}"
)

print(display_df.to_string(index=False))

# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

actual = df["Actual Freight"]
predicted = df["XGBoost Prediction"]

mae = np.mean(np.abs(predicted - actual))
rmse = np.sqrt(np.mean((predicted - actual) ** 2))
mape = np.mean(np.abs((predicted - actual) / actual)) * 100

lower_count = (predicted < actual).sum()

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

print(f"Months evaluated                 : {len(df)}")
print(f"Prediction lower than actual     : {lower_count} / {len(df)}")
print(f"Prediction higher than actual    : {len(df) - lower_count} / {len(df)}")
print(f"Average actual freight           : ${actual.mean():,.2f}/day")
print(f"Average XGBoost prediction       : ${predicted.mean():,.2f}/day")
print(f"Average prediction difference    : ${np.mean(predicted - actual):+,.2f}/day")
print(f"MAE                              : ${mae:,.2f}/day")
print(f"RMSE                             : ${rmse:,.2f}/day")
print(f"MAPE                             : {mape:.2f}%")

# ---------------------------------------------------------
# Save CSV
# ---------------------------------------------------------

output_path = Path("data/processed/xgboost_2024_actual_vs_predicted.csv")

df.to_csv(output_path, index=False)

print("\nSaved comparison to:")
print(output_path)