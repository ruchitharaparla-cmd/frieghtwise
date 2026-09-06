"""
Vessel Turnaround & Delay Risk Modeling Module for FreightWise Stage 3.

Evaluates CatBoost, XGBoost, and Random Forest baselines for:
1. Turnaround time regression (turnaround_time_hours)
2. Delay risk binary classification (delay_risk = 1 if turnaround > 50.0 hours)

Uses strict chronological train/validation/test splits on 669 Bulk Carrier records,
with zero leakage of target or post-event fields into classification features.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier, XGBRegressor

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

from .contracts import (
    DELAY_RISK_THRESHOLD_HOURS,
    VESSEL_CATEGORICAL_FEATURES,
    VESSEL_FEATURES_12,
    VESSEL_NUMERIC_FEATURES,
    VesselDatasetContract,
)

# Output Paths
VESSEL_TURNAROUND_MODEL_PATH: str = "ml/delays/vessel_turnaround_model.joblib"
VESSEL_DELAY_RISK_MODEL_PATH: str = "ml/delays/vessel_delay_risk_model.joblib"
VESSEL_COMPARISON_CSV_PATH: str = "data/processed/vessel_model_comparison.csv"


def create_vessel_preprocessor() -> ColumnTransformer:
    """
    Creates the standard ColumnTransformer for pre-voyage vessel features.
    """
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                VESSEL_CATEGORICAL_FEATURES,
            ),
            ("num", StandardScaler(), VESSEL_NUMERIC_FEATURES),
        ]
    )


def train_and_evaluate_vessel_models(
    loader: Optional[Any] = None,
    save_artifacts: bool = True,
) -> Dict[str, Any]:
    """
    Executes end-to-end training and evaluation for vessel turnaround time
    and delay risk classification.

    Parameters
    ----------
    loader : Optional[Any]
        DataLoader instance. If None, instantiates DataLoader.
    save_artifacts : bool
        Whether to save joblib model artifacts and comparison CSV.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing model selection results, metrics tables, and evaluation objects.
    """
    if loader is None:
        from src.data.loader import DataLoader
        loader = DataLoader()

    df_raw = loader.load_vessel_performance()

    # Reconcile raw dataset (2,736 rows) -> Bulk Carrier subset (669 rows)
    bulk_df = VesselDatasetContract.validate_and_filter_bulk_carriers(df_raw)

    # Add binary delay_risk target (project-defined modeling threshold: > 50.0 hours)
    bulk_df["delay_risk"] = (bulk_df["turnaround_time_hours"] > DELAY_RISK_THRESHOLD_HOURS).astype(int)

    # Chronological split (463 train / 101 val / 105 test)
    train_df, val_df, test_df = VesselDatasetContract.split_vessel_data_chronologically(bulk_df)

    # Extract X (strictly pre-voyage features) and y
    X_train = train_df[VESSEL_FEATURES_12]
    y_train_reg = train_df["turnaround_time_hours"]
    y_train_clf = train_df["delay_risk"]

    X_val = val_df[VESSEL_FEATURES_12]
    y_val_reg = val_df["turnaround_time_hours"]
    y_val_clf = val_df["delay_risk"]

    X_test = test_df[VESSEL_FEATURES_12]
    y_test_reg = test_df["turnaround_time_hours"]
    y_test_clf = test_df["delay_risk"]

    # =========================================================================
    # 1. Turnaround Time Regression Models
    # =========================================================================
    reg_models: Dict[str, Any] = {
        "Random Forest Regressor (Round 1 Baseline)": Pipeline([
            ("preprocessor", create_vessel_preprocessor()),
            ("model", RandomForestRegressor(n_estimators=300, max_depth=8, min_samples_leaf=2, random_state=42)),
        ]),
        "XGBoost Regressor": Pipeline([
            ("preprocessor", create_vessel_preprocessor()),
            ("model", XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)),
        ]),
    }

    if CATBOOST_AVAILABLE:
        reg_models["CatBoost Regressor"] = Pipeline([
            ("preprocessor", create_vessel_preprocessor()),
            ("model", CatBoostRegressor(iterations=300, depth=5, learning_rate=0.05, random_seed=42, verbose=0)),
        ])

    reg_results: List[Dict[str, Any]] = []
    trained_reg_pipelines: Dict[str, Any] = {}

    for name, pipeline in reg_models.items():
        pipeline.fit(X_train, y_train_reg)
        trained_reg_pipelines[name] = pipeline

        val_pred = pipeline.predict(X_val)
        val_mae = mean_absolute_error(y_val_reg, val_pred)
        val_rmse = np.sqrt(mean_squared_error(y_val_reg, val_pred))
        val_r2 = r2_score(y_val_reg, val_pred)

        test_pred = pipeline.predict(X_test)
        test_mae = mean_absolute_error(y_test_reg, test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test_reg, test_pred))
        test_r2 = r2_score(y_test_reg, test_pred)

        reg_results.append({
            "model_type": "Regression",
            "model_name": name,
            "val_mae": round(val_mae, 4),
            "val_rmse": round(val_rmse, 4),
            "val_r2": round(val_r2, 4),
            "test_mae": round(test_mae, 4),
            "test_rmse": round(test_rmse, 4),
            "test_r2": round(test_r2, 4),
        })

    # Select best regression model based exclusively on Validation MAE
    reg_results_sorted = sorted(reg_results, key=lambda x: x["val_mae"])
    best_reg_name = reg_results_sorted[0]["model_name"]
    best_reg_pipeline = trained_reg_pipelines[best_reg_name]

    # =========================================================================
    # 2. Delay Risk Classification Models
    # =========================================================================
    clf_models: Dict[str, Any] = {
        "Random Forest Classifier Baseline": Pipeline([
            ("preprocessor", create_vessel_preprocessor()),
            ("model", RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)),
        ]),
        "XGBoost Classifier": Pipeline([
            ("preprocessor", create_vessel_preprocessor()),
            ("model", XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss")),
        ]),
    }

    if CATBOOST_AVAILABLE:
        clf_models["CatBoost Classifier"] = Pipeline([
            ("preprocessor", create_vessel_preprocessor()),
            ("model", CatBoostClassifier(iterations=200, depth=4, learning_rate=0.05, random_seed=42, verbose=0)),
        ])

    clf_results: List[Dict[str, Any]] = []
    trained_clf_pipelines: Dict[str, Any] = {}

    for name, pipeline in clf_models.items():
        pipeline.fit(X_train, y_train_clf)
        trained_clf_pipelines[name] = pipeline

        val_pred = pipeline.predict(X_val)
        val_proba = pipeline.predict_proba(X_val)[:, 1] if hasattr(pipeline, "predict_proba") else val_pred

        val_f1 = f1_score(y_val_clf, val_pred, zero_division=0)
        val_prec = precision_score(y_val_clf, val_pred, zero_division=0)
        val_rec = recall_score(y_val_clf, val_pred, zero_division=0)
        val_auc = roc_auc_score(y_val_clf, val_proba) if len(np.unique(y_val_clf)) > 1 else 0.5

        test_pred = pipeline.predict(X_test)
        test_proba = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else test_pred

        test_f1 = f1_score(y_test_clf, test_pred, zero_division=0)
        test_prec = precision_score(y_test_clf, test_pred, zero_division=0)
        test_rec = recall_score(y_test_clf, test_pred, zero_division=0)
        test_auc = roc_auc_score(y_test_clf, test_proba) if len(np.unique(y_test_clf)) > 1 else 0.5

        clf_results.append({
            "model_type": "Classification",
            "model_name": name,
            "val_f1": round(val_f1, 4),
            "val_precision": round(val_prec, 4),
            "val_recall": round(val_rec, 4),
            "val_roc_auc": round(val_auc, 4),
            "test_f1": round(test_f1, 4),
            "test_precision": round(test_prec, 4),
            "test_recall": round(test_rec, 4),
            "test_roc_auc": round(test_auc, 4),
        })

    # Select best classification model based exclusively on Validation F1
    clf_results_sorted = sorted(clf_results, key=lambda x: x["val_f1"], reverse=True)
    best_clf_name = clf_results_sorted[0]["model_name"]
    best_clf_pipeline = trained_clf_pipelines[best_clf_name]

    # Save artifacts if requested
    if save_artifacts:
        os.makedirs(os.path.dirname(VESSEL_TURNAROUND_MODEL_PATH), exist_ok=True)
        joblib.dump(best_reg_pipeline, VESSEL_TURNAROUND_MODEL_PATH)
        joblib.dump(best_clf_pipeline, VESSEL_DELAY_RISK_MODEL_PATH)

        # Build comparison summary DataFrame and save
        all_summary = []
        for r in reg_results:
            all_summary.append({
                "model_type": "Regression",
                "model_name": r["model_name"],
                "primary_val_metric": f"MAE: {r['val_mae']}",
                "val_score": r["val_mae"],
                "test_score": r["test_mae"],
                "is_selected": (r["model_name"] == best_reg_name),
            })
        for c in clf_results:
            all_summary.append({
                "model_type": "Classification",
                "model_name": c["model_name"],
                "primary_val_metric": f"F1: {c['val_f1']}",
                "val_score": c["val_f1"],
                "test_score": c["test_f1"],
                "is_selected": (c["model_name"] == best_clf_name),
            })

        df_comp = pd.DataFrame(all_summary)
        os.makedirs(os.path.dirname(VESSEL_COMPARISON_CSV_PATH), exist_ok=True)
        df_comp.to_csv(VESSEL_COMPARISON_CSV_PATH, index=False)

    return {
        "best_regression_model_name": best_reg_name,
        "best_classification_model_name": best_clf_name,
        "regression_results": reg_results,
        "classification_results": clf_results,
        "best_regression_pipeline": best_reg_pipeline,
        "best_classification_pipeline": best_clf_pipeline,
    }
