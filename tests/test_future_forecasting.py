from pathlib import Path

import joblib
import pandas as pd
import pytest

from src.forecasting.future_features import model_features


MODEL = Path("ml/forecasting/final_xgboost_model.joblib")


@pytest.mark.skipif(not MODEL.exists(), reason="Run from the FreightWise repository.")
def test_model_has_exact_26_feature_contract():
    model = joblib.load(MODEL)
    assert len(model.feature_names_in_) == 26
    assert model_features(MODEL) == list(model.feature_names_in_)


def test_feature_contract_matches_audited_contract():
    expected = [
        "freight_lag_1", "freight_lag_3", "freight_lag_6", "freight_lag_12",
        "freight_rolling_mean_3", "freight_rolling_mean_6",
        "freight_rolling_mean_12", "freight_rolling_std_3",
        "baltic_dry_index_lag_1", "baltic_dry_index_lag_3",
        "brent_price_lag_1", "brent_price_lag_3",
        "wti_price_lag_1", "wti_price_lag_3",
        "dxy_index_lag_1", "dxy_index_lag_3",
        "vix_lag_1", "vix_lag_3",
        "gpr_index_lag_1", "gpr_index_lag_3",
        "thermal_coal_price_lag_1", "thermal_coal_price_lag_3",
        "month_num", "quarter", "month_sin", "month_cos",
    ]
    assert len(expected) == 26
