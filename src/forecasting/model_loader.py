"""
Model Loader Module for FreightWise Stage 2.4 — Freight Forecasting Production/Inference Layer.

Provides lazy, cached loading of the selected Round 1 XGBoost model artifact,
with integrity verification via SHA-256 checksum.
"""

import hashlib
import os
from typing import Any, List, Optional, Tuple

import joblib

# ---------------------------------------------------------------------------
# Default Constants
# ---------------------------------------------------------------------------
DEFAULT_XGBOOST_MODEL_PATH: str = "ml/forecasting/final_xgboost_model.joblib"

# Hard-coded SHA-256 checksum as regression guard (Requirement 5)
EXPECTED_XGBOOST_SHA256: str = "07820057afecbe0010dcc9fcf3bd7559d435bdfafee2336afa268bd1a3e41396"

# Module-level cache for singleton model instance
_CACHED_MODEL: Optional[Any] = None
_CACHED_VERSION: Optional[str] = None
_CACHED_PATH: Optional[str] = None


def compute_file_sha256(filepath: str) -> str:
    """
    Computes the SHA-256 hash of a file.

    Parameters
    ----------
    filepath : str
        Path to the target file.

    Returns
    -------
    str : Hexadecimal SHA-256 digest.
    """
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_xgboost_model(
    model_path: Optional[str] = None,
    verify_checksum: bool = True,
    force_reload: bool = False,
) -> Tuple[Any, str]:
    """
    Loads the production XGBoost forecasting model artifact lazily (singleton).

    Parameters
    ----------
    model_path : Optional[str]
        Path to the joblib artifact. If None, uses DEFAULT_XGBOOST_MODEL_PATH.
    verify_checksum : bool
        If True and using DEFAULT_XGBOOST_MODEL_PATH, verifies against EXPECTED_XGBOOST_SHA256.
    force_reload : bool
        If True, reloads from disk even if already cached.

    Returns
    -------
    Tuple[Any, str]
        (model_object, sha256_version_hash)

    Raises
    -------
    FileNotFoundError
        If the model artifact does not exist at the resolved path.
    ValueError
        If checksum verification fails or the model artifact has invalid attributes.
    """
    global _CACHED_MODEL, _CACHED_VERSION, _CACHED_PATH

    path = model_path or DEFAULT_XGBOOST_MODEL_PATH

    if (
        not force_reload
        and _CACHED_MODEL is not None
        and _CACHED_PATH == path
        and _CACHED_VERSION is not None
    ):
        return _CACHED_MODEL, _CACHED_VERSION

    if not os.path.exists(path):
        raise FileNotFoundError(f"XGBoost model artifact not found at: {path}")

    # Compute actual checksum
    file_sha256 = compute_file_sha256(path)

    if verify_checksum and path == DEFAULT_XGBOOST_MODEL_PATH:
        if file_sha256 != EXPECTED_XGBOOST_SHA256:
            raise ValueError(
                f"Model artifact integrity check failed! Expected SHA-256 "
                f"'{EXPECTED_XGBOOST_SHA256}', got '{file_sha256}'."
            )

    model = joblib.load(path)

    # Validate essential model attributes
    if not hasattr(model, "predict"):
        raise ValueError(f"Loaded object from {path} does not have a predict method.")

    if hasattr(model, "n_features_in_") and model.n_features_in_ != 26:
        raise ValueError(
            f"Expected model to require 26 features, but n_features_in_={model.n_features_in_}."
        )

    if not hasattr(model, "feature_names_in_"):
        raise ValueError("Model artifact is missing required feature_names_in_ attribute.")

    # Cache singleton
    _CACHED_MODEL = model
    _CACHED_VERSION = file_sha256
    _CACHED_PATH = path

    return model, file_sha256
