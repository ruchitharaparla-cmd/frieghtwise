import hashlib
from pathlib import Path
from typing import Any, Optional, Tuple

import joblib


MODEL_PATH = (
    Path(__file__).resolve().parents[3]
    / "ml"
    / "forecasting"
    / "final_xgboost_model.joblib"
)

EXPECTED_XGBOOST_SHA256 = (
    "07820057afecbe0010dcc9fcf3bd7559d435bdfafee2336afa268bd1a3e41396"
)

_cached_model: Optional[Any] = None
_cached_version: Optional[str] = None


def compute_file_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()

    with filepath.open("rb") as file:
        while chunk := file.read(65536):
            hasher.update(chunk)

    return hasher.hexdigest()


def load_xgboost_model() -> Tuple[Any, str]:
    global _cached_model, _cached_version

    if _cached_model is not None:
        return _cached_model, _cached_version

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"XGBoost model artifact not found: {MODEL_PATH}"
        )

    actual_checksum = compute_file_sha256(MODEL_PATH)

    if actual_checksum != EXPECTED_XGBOOST_SHA256:
        raise ValueError(
            "XGBoost model checksum verification failed. "
            f"Expected {EXPECTED_XGBOOST_SHA256}, "
            f"got {actual_checksum}."
        )

    model = joblib.load(MODEL_PATH)

    if not hasattr(model, "predict"):
        raise ValueError("Loaded forecasting artifact does not expose predict().")

    _cached_model = model
    _cached_version = actual_checksum

    return _cached_model, _cached_version
