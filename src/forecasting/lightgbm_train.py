"""
LightGBM Model Training and Evaluation Module for FreightWise Round 2 — Stage 2.2B.
Trains a deterministic LightGBM regression model on the 43-feature dataset,
using the validation set for early stopping and keeping the test set untouched until final evaluation.
Evaluates performance against Naive baseline and Round 1 XGBoost benchmark on identical 2024 test targets,
saves model artifact to ml/forecasting/lightgbm_freight_model.joblib, and exports predictions.

LightGBM 4.7.0 API NOTE: Uses eval_X / eval_y parameters for validation set monitoring
(the older eval_set parameter is deprecated in LightGBM 4.x and triggers LGBMDeprecationWarning).
"""

import os
import joblib
import pandas as pd
import numpy as np
import lightgbm as lgb
from typing import Dict, Any, Optional, Tuple

from .contracts import ForecastingDatasetContract, XGBOOST_26_FEATURES, DEFAULT_TARGET_COL, DEFAULT_DATE_COL
from .lightgbm_data import prepare_lightgbm_datasets, LightGBMSplitResult, LIGHTGBM_FEATURES
from .lightgbm_config import get_default_lightgbm_config, LightGBMModelConfig
from .metrics import calculate_all_metrics, calculate_mae, calculate_rmse, calculate_mape


DEFAULT_LIGHTGBM_MODEL_PATH = "ml/forecasting/lightgbm_freight_model.joblib"
DEFAULT_PREDICTIONS_PATH = "data/processed/lightgbm_forecast_predictions.csv"
BENCHMARK_XGBOOST_MODEL_PATH = "ml/forecasting/final_xgboost_model.joblib"


def train_and_evaluate_lightgbm(
    loader: Optional[Any] = None,
    config: Optional[LightGBMModelConfig] = None,
    save_model: bool = True,
    save_predictions: bool = True,
    model_output_path: str = DEFAULT_LIGHTGBM_MODEL_PATH,
    predictions_output_path: str = DEFAULT_PREDICTIONS_PATH,
    early_stopping_rounds: int = 15,
) -> Dict[str, Any]:
    """
    Trains and evaluates a LightGBM regression model for freight forecasting.

    Steps:
      1. Load Stage 2.2A prepared datasets (143 train, 12 val, 12 test; 43 features in X).
      2. Initialize LightGBMModelConfig (default conservative parameters).
      3. Fit LightGBM model on (X_train, y_train) using (X_val, y_val) for early stopping.
      4. Record best_iteration / best_iteration_.
      5. Evaluate LightGBM on train, validation, and test sets.
      6. Load benchmark Round 1 XGBoost model (read-only) and evaluate on identical y_test.
      7. Evaluate Naive baseline on identical y_test.
      8. Calculate LightGBM MAE & RMSE improvement percentages vs Naive and vs XGBoost.
      9. Save trained model binary to model_output_path (does NOT overwrite XGBoost model).
     10. Export prediction DataFrame with columns [date, actual, predicted, model, split] to predictions_output_path.
    """
    # 1. Prepare datasets
    split_res: LightGBMSplitResult = prepare_lightgbm_datasets(loader=loader)
    split_res.verify_no_leakage(target_col=DEFAULT_TARGET_COL)

    # 2. Get configuration
    model_cfg = config or get_default_lightgbm_config()
    model_params = model_cfg.to_dict()

    # 3. Train LightGBM regressor with early stopping on validation set ONLY
    # API NOTE (LightGBM 4.7.0): eval_set is deprecated; use eval_X / eval_y instead.
    # Early stopping is provided via lgb.early_stopping() callback — supported in 4.x.
    # This documents the actual installed API method per Requirement 7 (NO ASSUMPTIONS).
    lgb_regressor = lgb.LGBMRegressor(**model_params)

    # Fit using validation set for early stopping (test set remains 100% untouched)
    lgb_regressor.fit(
        split_res.X_train,
        split_res.y_train,
        eval_X=split_res.X_val,
        eval_y=split_res.y_val,
        callbacks=[lgb.early_stopping(stopping_rounds=early_stopping_rounds, verbose=False)],
    )

    # 4. Extract best_iteration
    best_iter = getattr(lgb_regressor, "best_iteration_", None)
    if best_iter is None:
        best_iter = getattr(lgb_regressor, "best_iteration", model_cfg.n_estimators)

    # 5. Predict and evaluate LightGBM on Train, Validation, and Test partitions
    pred_train = lgb_regressor.predict(split_res.X_train)
    pred_val = lgb_regressor.predict(split_res.X_val)
    pred_test = lgb_regressor.predict(split_res.X_test)

    metrics_train = calculate_all_metrics(split_res.y_train, pred_train)
    metrics_val = calculate_all_metrics(split_res.y_val, pred_val)
    metrics_test = calculate_all_metrics(split_res.y_test, pred_test)

    # 6. Evaluate Benchmark Round 1 XGBoost Model on identical test target (y_test)
    if not os.path.exists(BENCHMARK_XGBOOST_MODEL_PATH):
        raise FileNotFoundError(f"Benchmark XGBoost model missing at {BENCHMARK_XGBOOST_MODEL_PATH}")

    xgb_model = joblib.load(BENCHMARK_XGBOOST_MODEL_PATH)
    if hasattr(xgb_model, "feature_names_in_"):
        xgb_feats = list(xgb_model.feature_names_in_)
    else:
        xgb_feats = XGBOOST_26_FEATURES

    # Extract exact XGBoost input features from test split
    if loader is None:
        from src.data.loader import DataLoader
        loader = DataLoader()
    raw_fmf = loader.load_freight_model_features()
    # Align test split rows with raw_fmf to get full feature dataset
    test_dates = list(split_res.test_dates)
    test_fmf = raw_fmf[raw_fmf["date"].isin(test_dates)].copy().sort_values("date").reset_index(drop=True)
    X_test_xgb = ForecastingDatasetContract.extract_xgboost_features(test_fmf, feature_list=xgb_feats)

    pred_test_xgb = xgb_model.predict(X_test_xgb)
    metrics_xgb_test = calculate_all_metrics(split_res.y_test, pred_test_xgb)

    # 7. Evaluate Naive Baseline on identical test target (y_test)
    # Naive baseline predicts prior month's target value (y_{t-1})
    val_last_target = split_res.y_val.iloc[-1]
    pred_test_naive = np.array([val_last_target] + split_res.y_test.iloc[:-1].tolist())
    metrics_naive_test = calculate_all_metrics(split_res.y_test, pred_test_naive)

    # 8. Compute improvement metrics vs Naive and vs XGBoost on identical test set
    mae_imp_vs_naive = ((metrics_naive_test["MAE"] - metrics_test["MAE"]) / metrics_naive_test["MAE"]) * 100.0
    rmse_imp_vs_naive = ((metrics_naive_test["RMSE"] - metrics_test["RMSE"]) / metrics_naive_test["RMSE"]) * 100.0

    mae_imp_vs_xgb = ((metrics_xgb_test["MAE"] - metrics_test["MAE"]) / metrics_xgb_test["MAE"]) * 100.0
    rmse_imp_vs_xgb = ((metrics_xgb_test["RMSE"] - metrics_test["RMSE"]) / metrics_xgb_test["RMSE"]) * 100.0

    # 9. Save LightGBM model artifact if requested
    if save_model:
        os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
        joblib.dump(lgb_regressor, model_output_path)

    # 10. Construct prediction DataFrame and save to CSV if requested
    train_preds_df = pd.DataFrame({
        "date": split_res.train_dates.values,
        "actual": split_res.y_train.values,
        "predicted": pred_train,
        "model": "LightGBM",
        "split": "train",
    })

    val_preds_df = pd.DataFrame({
        "date": split_res.val_dates.values,
        "actual": split_res.y_val.values,
        "predicted": pred_val,
        "model": "LightGBM",
        "split": "validation",
    })

    test_preds_df = pd.DataFrame({
        "date": split_res.test_dates.values,
        "actual": split_res.y_test.values,
        "predicted": pred_test,
        "model": "LightGBM",
        "split": "test",
    })

    all_predictions_df = pd.concat([train_preds_df, val_preds_df, test_preds_df], ignore_index=True)

    if save_predictions:
        os.makedirs(os.path.dirname(predictions_output_path), exist_ok=True)
        all_predictions_df.to_csv(predictions_output_path, index=False)

    benchmark_comparison = {
        "Naive Baseline": metrics_naive_test,
        "Round 1 XGBoost": metrics_xgb_test,
        "Round 2 LightGBM": metrics_test,
    }

    improvements = {
        "mae_improvement_vs_naive_pct": mae_imp_vs_naive,
        "rmse_improvement_vs_naive_pct": rmse_imp_vs_naive,
        "mae_improvement_vs_xgb_pct": mae_imp_vs_xgb,
        "rmse_improvement_vs_xgb_pct": rmse_imp_vs_xgb,
    }

    return {
        "model": lgb_regressor,
        "lightgbm_config": model_params,
        "best_iteration": best_iter,
        "feature_count": len(LIGHTGBM_FEATURES),
        "feature_names": LIGHTGBM_FEATURES,
        "metrics": {
            "train": metrics_train,
            "validation": metrics_val,
            "test": metrics_test,
        },
        "benchmark_comparison": benchmark_comparison,
        "improvements": improvements,
        "model_path": model_output_path if save_model else None,
        "predictions_path": predictions_output_path if save_predictions else None,
        "predictions_df": all_predictions_df,
    }
