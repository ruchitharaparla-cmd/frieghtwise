"""
Test runner script for Stage 1 Data Foundation test suite.
Executes all 11 test functions natively without external test runner dependencies.
"""

import sys
import traceback
from tests.test_data_foundation import (
    loader,
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


def run_all_tests():
    tests = [
        ("Test 1: Freight Loader & Schema", test_freight_loader_and_schema),
        ("Test 2: Vessel Loader & Filtering", test_vessel_loader_and_filtering),
        ("Test 3: India Import Loader & Units", test_india_import_loader_units),
        ("Test 4: Schema Contracts Validation", test_schema_contracts),
        ("Test 5: Date Normalization & Immutability", test_date_normalization_and_copy_immutability),
        ("Test 6: Unit Validation Checks", test_unit_validation_checks),
        ("Test 7: Entity Normalization & Coal Separation", test_entity_normalization_and_coal_separation),
        ("Test 8: Route Demand Summary & Tag", test_route_demand_summary_loading),
        ("Test 9: Safe Temporal Joins", test_safe_temporal_joins),
        ("Test 10: Exact XGBoost Model Integrity", test_exact_xgboost_model_integrity),
        ("Test 11: Round 1 Source File Integrity", test_round1_source_file_integrity),
    ]

    print("=" * 70)
    print("RUNNING FREIGHTWISE STAGE 1 TEST SUITE")
    print("=" * 70)

    from src.data.loader import DataLoader
    ldr = DataLoader()
    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            if "loader" in test_fn.__code__.co_varnames:
                test_fn(ldr)
            else:
                test_fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            traceback.print_exc()
            failed += 1

    print("=" * 70)
    print(f"TEST SUMMARY: Total: {len(tests)}, Passed: {passed}, Failed: {failed}")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
