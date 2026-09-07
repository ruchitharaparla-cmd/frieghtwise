"""Regression checks for Stages 1-3 after Stage 4 implementation."""

import os

import pytest

from src.data.loader import DataLoader


class TestStage1DataLoaderUnmodified:
    def test_freight_model_features_loads(self):
        loader = DataLoader()
        dataframe = loader.load_freight_model_features()
        assert len(dataframe) > 0
        assert "bulk_carrier_handysize_usd_day" in dataframe.columns

    def test_vessel_performance_loads(self):
        loader = DataLoader()
        dataframe = loader.load_vessel_performance()
        assert len(dataframe) > 0
        assert "ship_type" in dataframe.columns
        assert "draft_meters" in dataframe.columns


class TestStage2ForecastingModelUnmodified:
    def test_xgboost_model_file_exists(self):
        path = "ml/forecasting/final_xgboost_model.joblib"
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0

    def test_lightgbm_model_file_exists(self):
        path = "ml/forecasting/lightgbm_freight_model.joblib"
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


class TestStage3DelayModelsUnmodified:
    def test_vessel_turnaround_models_exist(self):
        for path in (
            "ml/delays/vessel_turnaround_model.joblib",
            "ml/delays/vessel_delay_risk_model.joblib",
        ):
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0

    def test_port_congestion_models_exist(self):
        for path in (
            "ml/delays/port_congestion_regressor.joblib",
            "ml/delays/port_congestion_classifier.joblib",
        ):
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0


class TestNoDataModification:
    def test_route_demand_summary_intact(self):
        loader = DataLoader()
        dataframe = loader.load_route_demand_summary()
        assert len(dataframe) > 0
        assert "Country_of_Consignment" in dataframe.columns
        assert "Port" in dataframe.columns
        assert "demand_score" in dataframe.columns

    def test_vessel_performance_data_intact(self):
        loader = DataLoader()
        dataframe = loader.load_vessel_performance()
        required_columns = (
            "ship_type",
            "maintenance_status",
            "draft_meters",
            "cargo_weight_tons",
        )
        for column in required_columns:
            assert column in dataframe.columns
        assert len(dataframe) >= 2700


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
