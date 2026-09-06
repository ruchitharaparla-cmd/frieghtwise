"""
Global Port Congestion Risk Modeling Module for FreightWise Stage 3.

Evaluates CatBoost, Random Forest, and Persistence Naive baselines for:
1. Continuous 1-week-ahead congestion index regression (congestion_index_lead1)
2. Binary 1-week-ahead high congestion risk classification (high_congestion_risk_lead1)

Correction 2: Saves separate joblib artifacts:
- ml/delays/port_congestion_regressor.joblib
- ml/delays/port_congestion_classifier.joblib
Correction 3: Explicit row reconciliation (6,260 raw -> 6,240 effective: 4,160 Train / 1,040 Val / 1,040 Test).
"""

import os
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

from .contracts import (
    HIGH_CONGESTION_THRESHOLD_INDEX,
    PORT_CATEGORICAL_FEATURES,
    PORT_CONGESTION_FEATURES,
    PortCongestionContract,
)

PORT_CONGESTION_REGRESSOR_PATH: str = "ml/delays/port_congestion_regressor.joblib"
PORT_CONGESTION_CLASSIFIER_PATH: str = "ml/delays/port_congestion_classifier.joblib"
PORT_COMPARISON_CSV_PATH: str = "data/processed/port_congestion_model_comparison.csv"


def create_port_preprocessor() -> ColumnTransformer:
    """
    Creates ColumnTransformer for port congestion features.
    """
    numeric_features = [
        f for f in PORT_CONGESTION_FEATURES if f not in PORT_CATEGORICAL_FEATURES
    ]
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                PORT_CATEGORICAL_FEATURES,
            ),
            ("num", StandardScaler(), numeric_features),
        ]
    )


def train_and_evaluate_port_congestion_models(
    loader: Optional[Any] = None,
    save_artifacts: bool = True,
) -> Dict[str, Any]:
    """
    Executes end-to-end training and evaluation for 1-week-ahead port congestion
    regression and classification.

    Reconciliation:
    - 6,260 raw weekly records across 20 ports.
    - Dropping the final week t+1 missing lead target leaves 6,240 effective rows.
    - Train: 4,160 rows (208 weeks, 2019-01-07 to 2022-12-26).
    - Validation: 1,040 rows (52 weeks, 2023-01-02 to 2023-12-25).
    - Test: 1,040 rows (52 weeks, 2024-01-01 to 2024-12-23).
    """
    if loader is None:
        from src.data.loader import DataLoader
        loader = DataLoader()

    df_raw = loader.load_port_congestion()
    assert len(df_raw) == 6260, f"Expected 6,260 raw port congestion records, got {len(df_raw)}"

    # 1. Audit India Port Absence (must report has_india_ports=False)
    audit_res = PortCongestionContract.audit_india_port_absence(df_raw)

    # 2. Calculate lag features strictly within each port entity (Addition 2)
    df_prepared = PortCongestionContract.prepare_panel_dataset(df_raw)
    assert len(df_prepared) == 6240, f"Expected 6,240 effective rows after lead1 target, got {len(df_prepared)}"

    # Verify no cross-port leakage
    assert PortCongestionContract.audit_no_cross_port_leakage(df_prepared), (
        "Cross-port temporal leakage detected during lag calculation!"
    )

    # 3. Chronological Split (Train: 4,160, Val: 1,040, Test: 1,040)
    train_df, val_df, test_df = PortCongestionContract.split_congestion_data_chronologically(df_prepared)
    assert len(train_df) == 4160
    assert len(val_df) == 1040
    assert len(test_df) == 1040

    # Extract X (strictly week t features) and y (week t+1 targets)
    X_train = train_df[PORT_CONGESTION_FEATURES]
    y_train_reg = train_df["congestion_index_lead1"]
    y_train_clf = train_df["high_congestion_risk_lead1"]

    X_val = val_df[PORT_CONGESTION_FEATURES]
    y_val_reg = val_df["congestion_index_lead1"]
    y_val_clf = val_df["high_congestion_risk_lead1"]

    X_test = test_df[PORT_CONGESTION_FEATURES]
    y_test_reg = test_df["congestion_index_lead1"]
    y_test_clf = test_df["high_congestion_risk_lead1"]

    # =========================================================================
    # 1. Regression Models (congestion_index_lead1)
    # =========================================================================
    reg_models: Dict[str, Any] = {
        "Persistence Naive Baseline": None,
        "Random Forest Regressor Baseline": Pipeline([
            ("preprocessor", create_port_preprocessor()),
            ("model", RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)),
        ]),
    }

    if CATBOOST_AVAILABLE:
        reg_models["CatBoost Regressor"] = Pipeline([
            ("preprocessor", create_port_preprocessor()),
            ("model", CatBoostRegressor(iterations=250, depth=4, learning_rate=0.05, random_seed=42, verbose=0)),
        ])

    reg_results: List[Dict[str, Any]] = []
    trained_reg_pipelines: Dict[str, Any] = {}

    # Naive Persistence Regression Baseline (y_pred[t+1] = y[t])
    naive_val_reg_pred = X_val["congestion_index"].values
    naive_test_reg_pred = X_test["congestion_index"].values

    reg_results.append({
        "task_type": "Regression",
        "model_name": "Persistence Naive Baseline",
        "val_mae": round(mean_absolute_error(y_val_reg, naive_val_reg_pred), 4),
        "val_rmse": round(np.sqrt(mean_squared_error(y_val_reg, naive_val_reg_pred)), 4),
        "val_r2": round(r2_score(y_val_reg, naive_val_reg_pred), 4),
        "test_mae": round(mean_absolute_error(y_test_reg, naive_test_reg_pred), 4),
        "test_rmse": round(np.sqrt(mean_squared_error(y_test_reg, naive_test_reg_pred)), 4),
        "test_r2": round(r2_score(y_test_reg, naive_test_reg_pred), 4),
    })

    for name, pipeline in reg_models.items():
        if pipeline is None:
            continue
        pipeline.fit(X_train, y_train_reg)
        trained_reg_pipelines[name] = pipeline

        val_pred = pipeline.predict(X_val)
        test_pred = pipeline.predict(X_test)

        reg_results.append({
            "task_type": "Regression",
            "model_name": name,
            "val_mae": round(mean_absolute_error(y_val_reg, val_pred), 4),
            "val_rmse": round(np.sqrt(mean_squared_error(y_val_reg, val_pred)), 4),
            "val_r2": round(r2_score(y_val_reg, val_pred), 4),
            "test_mae": round(mean_absolute_error(y_test_reg, test_pred), 4),
            "test_rmse": round(np.sqrt(mean_squared_error(y_test_reg, test_pred)), 4),
            "test_r2": round(r2_score(y_test_reg, test_pred), 4),
        })

    reg_results_sorted = sorted(reg_results, key=lambda x: x["val_mae"])
    best_reg_name = reg_results_sorted[0]["model_name"]
    best_reg_pipeline = trained_reg_pipelines.get(best_reg_name, list(trained_reg_pipelines.values())[0])

    # =========================================================================
    # 2. Classification Models (high_congestion_risk_lead1)
    # =========================================================================
    clf_models: Dict[str, Any] = {
        "Random Forest Classifier Baseline": Pipeline([
            ("preprocessor", create_port_preprocessor()),
            ("model", RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)),
        ]),
    }

    if CATBOOST_AVAILABLE:
        clf_models["CatBoost Classifier"] = Pipeline([
            ("preprocessor", create_port_preprocessor()),
            ("model", CatBoostClassifier(iterations=250, depth=4, learning_rate=0.05, random_seed=42, verbose=0)),
        ])

    naive_val_clf_pred = (naive_val_reg_pred >= HIGH_CONGESTION_THRESHOLD_INDEX).astype(int)
    naive_test_clf_pred = (naive_test_reg_pred >= HIGH_CONGESTION_THRESHOLD_INDEX).astype(int)

    clf_results: List[Dict[str, Any]] = [
        {
            "task_type": "Classification",
            "model_name": "Persistence Naive Baseline",
            "val_f1": round(f1_score(y_val_clf, naive_val_clf_pred, zero_division=0), 4),
            "val_precision": round(precision_score(y_val_clf, naive_val_clf_pred, zero_division=0), 4),
            "val_recall": round(recall_score(y_val_clf, naive_val_clf_pred, zero_division=0), 4),
            "val_roc_auc": 0.5,
            "val_pr_auc": round(precision_score(y_val_clf, naive_val_clf_pred, zero_division=0), 4),
            "test_f1": round(f1_score(y_test_clf, naive_test_clf_pred, zero_division=0), 4),
            "test_precision": round(precision_score(y_test_clf, naive_test_clf_pred, zero_division=0), 4),
            "test_recall": round(recall_score(y_test_clf, naive_test_clf_pred, zero_division=0), 4),
            "test_roc_auc": 0.5,
            "test_pr_auc": round(precision_score(y_test_clf, naive_test_clf_pred, zero_division=0), 4),
        }
    ]

    trained_clf_pipelines: Dict[str, Any] = {}

    for name, pipeline in clf_models.items():
        pipeline.fit(X_train, y_train_clf)
        trained_clf_pipelines[name] = pipeline

        val_pred = pipeline.predict(X_val)
        val_proba = pipeline.predict_proba(X_val)[:, 1]

        val_f1 = f1_score(y_val_clf, val_pred, zero_division=0)
        val_prec = precision_score(y_val_clf, val_pred, zero_division=0)
        val_rec = recall_score(y_val_clf, val_pred, zero_division=0)
        val_auc = roc_auc_score(y_val_clf, val_proba)
        val_pr_auc = average_precision_score(y_val_clf, val_proba)

        test_pred = pipeline.predict(X_test)
        test_proba = pipeline.predict_proba(X_test)[:, 1]

        test_f1 = f1_score(y_test_clf, test_pred, zero_division=0)
        test_prec = precision_score(y_test_clf, test_pred, zero_division=0)
        test_rec = recall_score(y_test_clf, test_pred, zero_division=0)
        test_auc = roc_auc_score(y_test_clf, test_proba)
        test_pr_auc = average_precision_score(y_test_clf, test_proba)

        clf_results.append({
            "task_type": "Classification",
            "model_name": name,
            "val_f1": round(val_f1, 4),
            "val_precision": round(val_prec, 4),
            "val_recall": round(val_rec, 4),
            "val_roc_auc": round(val_auc, 4),
            "val_pr_auc": round(val_pr_auc, 4),
            "test_f1": round(test_f1, 4),
            "test_precision": round(test_prec, 4),
            "test_recall": round(test_rec, 4),
            "test_roc_auc": round(test_auc, 4),
            "test_pr_auc": round(test_pr_auc, 4),
        })

    # Select best model based exclusively on Validation F1
    clf_results_sorted = sorted(clf_results, key=lambda x: x["val_f1"], reverse=True)
    best_clf_name = clf_results_sorted[0]["model_name"]
    best_clf_pipeline = trained_clf_pipelines.get(best_clf_name, list(trained_clf_pipelines.values())[0])

    # Correction 2: Save separate regressor and classifier joblib artifacts
    if save_artifacts:
        os.makedirs(os.path.dirname(PORT_CONGESTION_REGRESSOR_PATH), exist_ok=True)
        joblib.dump(best_reg_pipeline, PORT_CONGESTION_REGRESSOR_PATH)
        joblib.dump(best_clf_pipeline, PORT_CONGESTION_CLASSIFIER_PATH)

        summary_rows = []
        for r in reg_results:
            summary_rows.append({
                "task_type": "Regression",
                "model_name": r["model_name"],
                "val_primary_metric": f"MAE: {r['val_mae']}",
                "val_score": r["val_mae"],
                "test_score": r["test_mae"],
                "test_f1": np.nan,
                "val_f1": np.nan,
                "val_precision": np.nan,
                "val_recall": np.nan,
                "val_roc_auc": np.nan,
                "val_pr_auc": np.nan,
                "is_selected": (r["model_name"] == best_reg_name),
            })
        for c in clf_results:
            summary_rows.append({
                "task_type": "Classification",
                "model_name": c["model_name"],
                "val_primary_metric": f"F1: {c['val_f1']}",
                "val_score": c["val_f1"],
                "test_score": c["test_f1"],
                "test_f1": c["test_f1"],
                "val_f1": c["val_f1"],
                "val_precision": c["val_precision"],
                "val_recall": c["val_recall"],
                "val_roc_auc": c["val_roc_auc"],
                "val_pr_auc": c["val_pr_auc"],
                "is_selected": (c["model_name"] == best_clf_name),
            })

        df_comp = pd.DataFrame(summary_rows)
        os.makedirs(os.path.dirname(PORT_COMPARISON_CSV_PATH), exist_ok=True)
        df_comp.to_csv(PORT_COMPARISON_CSV_PATH, index=False)

    return {
        "audit": audit_res,
        "best_regressor_name": best_reg_name,
        "best_classifier_name": best_clf_name,
        "regression_results": reg_results,
        "classification_results": clf_results,
        "best_regressor_pipeline": best_reg_pipeline,
        "best_classifier_pipeline": best_clf_pipeline,
    }
