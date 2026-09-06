"""
Test runner script for FreightWise Round 2 — Stage 1, Stage 2.1, and Stage 2.2A Test Suites.
Executes all 34 test functions natively without external test runner dependencies.
"""

import sys
import traceback
from tests.test_data_foundation import (
    test_freight_loader_and_schema,
    test_vessel_loader_and_filtering,
    test_india_import_loader_units,
    test_schema_contracts,
    test_date_normalization_and_copy_immutability,
    test_unit_validation_checks,
    test_entity_normalization_and_coal_separation,
    test_route_demand_summary_loading,
    test_safe_temporal_joins,
    test_exact_xgboost_model_integrity,
    test_round1_source_file_integrity,
)
from tests.test_forecasting_stage2 import (
    test_chronological_split_sizes_and_ordering,
    test_no_train_val_test_overlap_and_leakage,
    test_metric_calculations_analytical,
    test_forecasting_contracts_and_xgboost_isolation,
    test_source_file_immutability,
)
from tests.test_lightgbm_stage2_2a import (
    test_lightgbm_dataset_loading,
    test_target_column_existence,
    test_target_separated_from_x,
    test_date_separated_from_x,
    test_all_features_numeric,
    test_explicit_feature_contract_match,
    test_target_not_in_feature_contract,
    test_raw_date_not_in_feature_contract,
    test_temporal_leakage_audit,
    test_preprocessing_no_leakage,
    test_chronological_split_sizes,
    test_train_dates_precede_val_dates,
    test_val_dates_precede_test_dates,
    test_zero_temporal_overlap,
    test_source_csv_immutability,
    test_round1_xgboost_model_immutability,
    test_xgboost_26_feature_contract_immutability,
    test_lightgbm_config_validity,
)


def run_all_tests():
    tests = [
        # Stage 1: Data Foundation Tests
        ("Stage 1 - Test 1: Freight Loader & Schema", test_freight_loader_and_schema),
        ("Stage 1 - Test 2: Vessel Loader & Filtering", test_vessel_loader_and_filtering),
        ("Stage 1 - Test 3: India Import Loader & Units", test_india_import_loader_units),
        ("Stage 1 - Test 4: Schema Contracts Validation", test_schema_contracts),
        ("Stage 1 - Test 5: Date Normalization & Immutability", test_date_normalization_and_copy_immutability),
        ("Stage 1 - Test 6: Unit Validation Checks", test_unit_validation_checks),
        ("Stage 1 - Test 7: Entity Normalization & Coal Separation", test_entity_normalization_and_coal_separation),
        ("Stage 1 - Test 8: Route Demand Summary & Tag", test_route_demand_summary_loading),
        ("Stage 1 - Test 9: Safe Temporal Joins", test_safe_temporal_joins),
        ("Stage 1 - Test 10: Exact XGBoost Model Integrity", test_exact_xgboost_model_integrity),
        ("Stage 1 - Test 11: Round 1 Source File Integrity", test_round1_source_file_integrity),
        # Stage 2.1: Freight Forecasting Contract & Foundation Tests
        ("Stage 2.1 - Test 12: Chronological Split Sizes & Ordering", test_chronological_split_sizes_and_ordering),
        ("Stage 2.1 - Test 13: Zero Overlap & Temporal Leakage Guard", test_no_train_val_test_overlap_and_leakage),
        ("Stage 2.1 - Test 14: Analytical Metric Calculations (MAE, RMSE, MAPE)", test_metric_calculations_analytical),
        ("Stage 2.1 - Test 15: Forecasting Contracts & XGBoost 26-Feature Separation", test_forecasting_contracts_and_xgboost_isolation),
        ("Stage 2.1 - Test 16: Round 1 Source File & Model Immutability", test_source_file_immutability),
        # Stage 2.2A: LightGBM Freight Forecasting Foundation Tests
        ("Stage 2.2A - Test 17: LightGBM Dataset Loading", test_lightgbm_dataset_loading),
        ("Stage 2.2A - Test 18: Target Column Existence", test_target_column_existence),
        ("Stage 2.2A - Test 19: Target Separation from X", test_target_separated_from_x),
        ("Stage 2.2A - Test 20: Date Metadata Separation from X", test_date_separated_from_x),
        ("Stage 2.2A - Test 21: 100% Numeric Feature Matrix Verification", test_all_features_numeric),
        ("Stage 2.2A - Test 22: Explicit LIGHTGBM_FEATURES Contract Match (43 features)", test_explicit_feature_contract_match),
        ("Stage 2.2A - Test 23: Target Non-presence in Feature Contract", test_target_not_in_feature_contract),
        ("Stage 2.2A - Test 24: Raw Date Non-presence in Feature Contract", test_raw_date_not_in_feature_contract),
        ("Stage 2.2A - Test 25: Temporal Leakage Audit on Features", test_temporal_leakage_audit),
        ("Stage 2.2A - Test 26: Preprocessing Leakage Guard", test_preprocessing_no_leakage),
        ("Stage 2.2A - Test 27: Chronological Split Sizes (143/12/12)", test_chronological_split_sizes),
        ("Stage 2.2A - Test 28: Train Dates Precede Validation Dates", test_train_dates_precede_val_dates),
        ("Stage 2.2A - Test 29: Validation Dates Precede Test Dates", test_val_dates_precede_test_dates),
        ("Stage 2.2A - Test 30: Zero Temporal Overlap Across Partitions", test_zero_temporal_overlap),
        ("Stage 2.2A - Test 31: Stage 1 Source CSV Immutability", test_source_csv_immutability),
        ("Stage 2.2A - Test 32: Round 1 XGBoost Model Immutability", test_round1_xgboost_model_immutability),
        ("Stage 2.2A - Test 33: XGBoost 26-Feature Contract Immutability", test_xgboost_26_feature_contract_immutability),
        ("Stage 2.2A - Test 34: LightGBMModelConfig Validation & Parameters", test_lightgbm_config_validity),
    ]

    print("=" * 80)
    print("RUNNING FREIGHTWISE TEST SUITE (STAGE 1, STAGE 2.1 & STAGE 2.2A)")
    print("=" * 80)

    from src.data.loader import DataLoader
    ldr = DataLoader()
    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            pos_args = test_fn.__code__.co_varnames[:test_fn.__code__.co_argcount]
            if "loader" in pos_args:
                test_fn(ldr)
            else:
                test_fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            traceback.print_exc()
            failed += 1

    print("=" * 80)
    print(f"TEST SUMMARY: Total: {len(tests)}, Passed: {passed}, Failed: {failed}")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
