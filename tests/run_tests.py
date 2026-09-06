"""
Test runner script for FreightWise Round 2 — Stage 1 & Stage 2 Test Suites.
Executes all 16 test functions natively without external test runner dependencies.
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
        ("Stage 2 - Test 12: Chronological Split Sizes & Ordering", test_chronological_split_sizes_and_ordering),
        ("Stage 2 - Test 13: Zero Overlap & Temporal Leakage Guard", test_no_train_val_test_overlap_and_leakage),
        ("Stage 2 - Test 14: Analytical Metric Calculations (MAE, RMSE, MAPE)", test_metric_calculations_analytical),
        ("Stage 2 - Test 15: Forecasting Contracts & XGBoost 26-Feature Separation", test_forecasting_contracts_and_xgboost_isolation),
        ("Stage 2 - Test 16: Round 1 Source File & Model Immutability", test_source_file_immutability),
    ]

    print("=" * 75)
    print("RUNNING FREIGHTWISE TEST SUITE (STAGE 1 & STAGE 2.1)")
    print("=" * 75)

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

    print("=" * 75)
    print(f"TEST SUMMARY: Total: {len(tests)}, Passed: {passed}, Failed: {failed}")
    print("=" * 75)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

