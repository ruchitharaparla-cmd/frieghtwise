from pathlib import Path

import pandas as pd

from src.decision.risk_idle import (
    build_analysis as build_risk_analysis,
)

from src.decision.market_entry import (
    build_analysis as build_market_analysis,
)

from src.decision.contract_optimizer import (
    ContractInput,
    optimize_contract,
)

from src.decision.commercial_adapter import (
    build_contract_input_from_forecast,
)

from src.decision.vessel_port_feasibility import (
    VesselInput,
    evaluate_vessel,
)

from src.decision.vessel_type_optimizer import (
    VesselCandidate,
    optimize_vessel_type,
)


OUTPUT_FILE = Path(
    "data/processed/freightwise_decision_output.csv"
)


def run_decision_pipeline(
    vessel: VesselInput,
    port_name: str,
    commercial_input: ContractInput | None = None,
    vessel_candidates: list[VesselCandidate] | None = None,
):
    """
    Run the complete FreightWise decision pipeline.

    Forecast
        ↓
    Risk + Idle Management
        ↓
    Market Entry
        ↓
    Vessel Type Optimization
        ↓
    Vessel + Port Feasibility
        ↓
    Contract Optimization
        ↓
    Final Recommendation

    vessel:
        Existing single-vessel input. Kept for backward compatibility.

    vessel_candidates:
        Optional list of vessel candidates. When supplied, FreightWise
        compares them and selects the best feasible vessel type.
    """

    # =========================================================
    # 1. RISK + IDLE MANAGEMENT
    # =========================================================

    risk_data = build_risk_analysis()

    if risk_data.empty:
        raise ValueError(
            "Risk + Idle analysis returned no data."
        )

    risk_data["date"] = pd.to_datetime(
        risk_data["date"]
    )

    # =========================================================
    # 2. MARKET ENTRY
    # =========================================================

    market_data = build_market_analysis()

    if market_data.empty:
        raise ValueError(
            "Market Entry analysis returned no data."
        )

    market_data["date"] = pd.to_datetime(
        market_data["date"]
    )

    # ---------------------------------------------------------
    # Select the latest market row having both 3M and 6M
    # forecast horizons.
    # ---------------------------------------------------------

    market_candidates = market_data[
        market_data["expected_change_3m_pct"].notna()
        & market_data["expected_change_6m_pct"].notna()
    ].sort_values("date")

    if market_candidates.empty:
        raise ValueError(
            "No market-entry row has sufficient "
            "3-month and 6-month forecast horizon."
        )

    latest_market = market_candidates.iloc[-1]

    decision_date = pd.Timestamp(
        latest_market["date"]
    )

    # =========================================================
    # 3. MATCH RISK DATA TO DECISION DATE
    # =========================================================

    matching_risk = risk_data[
        risk_data["date"] == decision_date
    ]

    if matching_risk.empty:
        latest_risk = None
    else:
        latest_risk = matching_risk.iloc[-1]

    def risk_value(column):
        """
        Safely return a risk field.

        Returns None when matching risk data is unavailable.
        """

        if latest_risk is None:
            return None

        return latest_risk.get(
            column,
            None,
        )

    # =========================================================
    # 4. VESSEL TYPE OPTIMIZATION
    # =========================================================

    vessel_optimization = None

    if vessel_candidates is not None:

        if not vessel_candidates:
            raise ValueError(
                "vessel_candidates cannot be empty."
            )

        # Cargo quantity is taken from the commercial input
        # only when it is available through the pipeline.
        #
        # Since ContractInput does not contain cargo quantity,
        # use the vessel DWT as a backward-compatible fallback
        # only for this direct test interface.
        #
        # The backend can later pass an explicit cargo quantity.
        cargo_tons = float(vessel.dwt_tons)

        vessel_optimization = optimize_vessel_type(
            cargo_tons=cargo_tons,
            port_name=port_name,
            candidates=vessel_candidates,
        )

        recommended_vessel = (
            vessel_optimization["recommended_vessel"]
        )

        if recommended_vessel is not None:

            vessel = VesselInput(
                vessel_name=recommended_vessel[
                    "vessel_name"
                ],
                vessel_type=recommended_vessel[
                    "vessel_type"
                ],
                dwt_tons=recommended_vessel[
                    "dwt_tons"
                ],
                loa_m=next(
                    candidate.loa_m
                    for candidate in vessel_candidates
                    if candidate.vessel_name
                    == recommended_vessel[
                        "vessel_name"
                    ]
                ),
                beam_m=next(
                    candidate.beam_m
                    for candidate in vessel_candidates
                    if candidate.vessel_name
                    == recommended_vessel[
                        "vessel_name"
                    ]
                ),
                draft_m=next(
                    candidate.draft_m
                    for candidate in vessel_candidates
                    if candidate.vessel_name
                    == recommended_vessel[
                        "vessel_name"
                    ]
                ),
            )

    # =========================================================
    # 5. VESSEL + PORT FEASIBILITY
    # =========================================================

    feasibility = evaluate_vessel(
        vessel,
        port_name=port_name,
    )

    if feasibility.empty:
        raise ValueError(
            f"No feasibility result for port: {port_name}"
        )

    selected_port = feasibility.iloc[0]

    port_feasible = (
        selected_port["status"] == "FEASIBLE"
    )

    # =========================================================
    # 6. CONTRACT OPTIMIZATION
    # =========================================================

    contract_result = None

    if commercial_input is not None:

        # -----------------------------------------------------
        # The ML forecast becomes the expected future spot rate.
        #
        # Commercial/backend inputs remain:
        # - current spot rate
        # - contract rate
        # - voyages
        # - voyage duration
        # - contract duration
        # -----------------------------------------------------

        future_forecast_rate = float(
            latest_market[
                "predicted_freight_usd_day"
            ]
        )

        # Use matching-date risk when available.
        # Otherwise preserve the explicitly supplied risk.
        if (
            latest_risk is not None
            and pd.notna(
                latest_risk.get(
                    "overall_risk_score"
                )
            )
        ):

            contract_risk_score = float(
                latest_risk[
                    "overall_risk_score"
                ]
            )

        else:

            contract_risk_score = float(
                commercial_input.risk_score
            )

        contract_input = (
            build_contract_input_from_forecast(
                current_spot_rate_usd_day=(
                    commercial_input
                    .current_spot_rate_usd_day
                ),

                contract_rate_usd_day=(
                    commercial_input
                    .contract_rate_usd_day
                ),

                voyages=(
                    commercial_input.voyages
                ),

                voyage_days=(
                    commercial_input.voyage_days
                ),

                contract_months=(
                    commercial_input.contract_months
                ),

                expected_future_spot_rate_usd_day=(
                    future_forecast_rate
                ),

                risk_score=(
                    contract_risk_score
                ),
            )
        )

        contract_result = optimize_contract(
            contract_input
        )

    # =========================================================
    # 7. FINAL MARKET RECOMMENDATION
    # =========================================================

    market_signal = latest_market[
        "market_entry_signal"
    ]

    # ---------------------------------------------------------
    # Feasibility has priority.
    #
    # An infeasible vessel can never be recommended.
    # ---------------------------------------------------------

    if not port_feasible:

        final_recommendation = (
            "DO NOT CHARTER"
        )

        final_reason = (
            "Selected vessel is not feasible at "
            "the selected port. Choose another "
            "feasible vessel or review the route."
        )

    else:

        final_recommendation = market_signal

        if latest_risk is None:

            final_reason = (
                "Selected vessel is feasible at the "
                "selected port. Market forecast is "
                "available, but risk data is unavailable "
                "for the forecast decision date."
            )

        else:

            final_reason = (
                "Selected vessel is feasible at the "
                "selected port and matching risk data "
                "is available. Market conditions determine "
                "the entry recommendation."
            )

    # =========================================================
    # 8. BUILD FINAL RESULT
    # =========================================================

    result = {

        # -----------------------------------------------------
        # Final decision
        # -----------------------------------------------------

        "decision_date":
            decision_date,

        "final_recommendation":
            final_recommendation,

        "final_reason":
            final_reason,

        # -----------------------------------------------------
        # Forecast
        # -----------------------------------------------------

        "forecast_date":
            latest_market["date"],

        "forecast_freight_usd_day":
            latest_market[
                "predicted_freight_usd_day"
            ],

        "freight_attractiveness_score":
            latest_market[
                "freight_attractiveness_score"
            ],

        "forecast_3m_avg":
            latest_market[
                "forecast_3m_avg"
            ],

        "forecast_6m_avg":
            latest_market[
                "forecast_6m_avg"
            ],

        "expected_change_3m_pct":
            latest_market[
                "expected_change_3m_pct"
            ],

        "expected_change_6m_pct":
            latest_market[
                "expected_change_6m_pct"
            ],

        "market_pressure_score":
            latest_market[
                "market_pressure_score"
            ],

        "forecast_data_status":
            latest_market.get(
                "data_status",
                None,
            ),

        "forecast_model":
            latest_market.get(
                "model_name",
                "XGBoost",
            ),

        # -----------------------------------------------------
        # Risk
        # -----------------------------------------------------

        "risk_data_available":
            latest_risk is not None,

        "risk_data_date":
            (
                decision_date
                if latest_risk is not None
                else None
            ),

        "market_risk_score":
            risk_value(
                "market_risk_score"
            ),

        "port_risk_score":
            risk_value(
                "port_risk_score"
            ),

        "overall_risk_score":
            risk_value(
                "overall_risk_score"
            ),

        "risk_level":
            risk_value(
                "risk_level"
            ),

        # -----------------------------------------------------
        # Idle management
        # -----------------------------------------------------

        "idle_risk_score":
            risk_value(
                "idle_risk_score"
            ),

        "idle_risk_level":
            risk_value(
                "idle_risk_level"
            ),

        "data_availability":
            risk_value(
                "data_availability"
            ),

        "annual_demand_risk_level":
            risk_value(
                "annual_demand_risk_level"
            ),

        "combined_idle_demand_risk_score":
            risk_value(
                "combined_idle_demand_risk_score"
            ),

        "combined_idle_demand_risk_level":
            risk_value(
                "combined_idle_demand_risk_level"
            ),

        "low_demand_period":
            risk_value(
                "low_demand_period"
            ),

        "alternative_employment_signal":
            risk_value(
                "alternative_employment_signal"
            ),

        "deadheading_risk":
            risk_value(
                "deadheading_risk"
            ),

        "highest_demand_alternative_port":
            risk_value(
                "highest_demand_alternative_port"
            ),

        "positioning_action":
            risk_value(
                "positioning_action"
            ),

        "idle_management_recommendation":
            risk_value(
                "idle_management_recommendation"
            ),

        # -----------------------------------------------------
        # Market entry
        # -----------------------------------------------------

        "market_entry_signal":
            latest_market[
                "market_entry_signal"
            ],

        "market_contract_strategy":
            latest_market[
                "contract_strategy"
            ],

        # -----------------------------------------------------
        # Vessel optimization
        # -----------------------------------------------------

        "vessel_optimization_used":
            vessel_optimization is not None,

        "recommended_vessel_type":
            (
                vessel_optimization[
                    "recommendation"
                ]
                if vessel_optimization is not None
                else None
            ),

        "recommended_vessel_name":
            (
                vessel_optimization[
                    "recommended_vessel"
                ]["vessel_name"]
                if (
                    vessel_optimization is not None
                    and vessel_optimization[
                        "recommended_vessel"
                    ] is not None
                )
                else None
            ),

        "recommended_vessel_suitability_score":
            (
                vessel_optimization[
                    "recommended_vessel"
                ]["suitability_score"]
                if (
                    vessel_optimization is not None
                    and vessel_optimization[
                        "recommended_vessel"
                    ] is not None
                )
                else None
            ),

        # -----------------------------------------------------
        # Vessel + port
        # -----------------------------------------------------

        "port":
            selected_port.get(
                "port"
            ),

        "vessel":
            selected_port.get(
                "vessel"
            ),

        "vessel_type":
            selected_port.get(
                "vessel_type"
            ),

        "port_feasibility":
            selected_port.get(
                "status"
            ),

        "feasibility_score":
            selected_port.get(
                "feasibility_score"
            ),

        "port_data_status":
            selected_port.get(
                "port_data_status"
            ),

        "feasibility_reason":
            selected_port.get(
                "reason"
            ),
    }

    # =========================================================
    # 9. ADD VESSEL CANDIDATE COMPARISON
    # =========================================================

    if vessel_optimization is not None:

        result[
            "vessel_candidate_count"
        ] = len(
            vessel_optimization[
                "candidates"
            ]
        )

        result[
            "feasible_vessel_count"
        ] = sum(
            candidate[
                "feasibility_status"
            ] == "FEASIBLE"
            for candidate
            in vessel_optimization[
                "candidates"
            ]
        )

    else:

        result[
            "vessel_candidate_count"
        ] = 1

        result[
            "feasible_vessel_count"
        ] = (
            1
            if port_feasible
            else 0
        )

    # =========================================================
    # 10. ADD CONTRACT RESULTS
    # =========================================================

    if contract_result is not None:

        result.update(
            {
                "contract_recommendation":
                    contract_result.get(
                        "recommendation"
                    ),

                "contract_type":
                    contract_result.get(
                        "contract_strategy"
                    ),

                "contract_months":
                    contract_result.get(
                        "contract_months"
                    ),

                "contract_voyages":
                    contract_result.get(
                        "voyages"
                    ),

                "voyage_days":
                    contract_result.get(
                        "voyage_days"
                    ),

                "current_spot_rate_usd_day":
                    contract_result.get(
                        "current_spot_rate_usd_day"
                    ),

                "contract_rate_usd_day":
                    contract_result.get(
                        "contract_rate_usd_day"
                    ),

                "expected_future_spot_rate_usd_day":
                    contract_result.get(
                        "expected_future_spot_rate_usd_day"
                    ),

                "spot_cost":
                    contract_result.get(
                        "spot_cost"
                    ),

                "future_spot_cost":
                    contract_result.get(
                        "future_spot_cost"
                    ),

                "contract_cost":
                    contract_result.get(
                        "contract_cost"
                    ),

                "expected_savings":
                    contract_result.get(
                        "savings_vs_current_spot"
                    ),

                "savings_percentage":
                    contract_result.get(
                        "savings_percentage"
                    ),

                "risk_premium":
                    contract_result.get(
                        "risk_premium"
                    ),

                "risk_adjusted_future_spot_cost":
                    contract_result.get(
                        "risk_adjusted_future_spot_cost"
                    ),
            }
        )

    # =========================================================
    # 11. FINAL FEASIBILITY OVERRIDE
    # =========================================================

    # An infeasible vessel can never be chartered,
    # regardless of market or contract recommendation.

    if not port_feasible:

        result[
            "final_recommendation"
        ] = "DO NOT CHARTER"

        result[
            "final_reason"
        ] = (
            "Selected vessel is not feasible at "
            "the selected port. Choose another "
            "feasible vessel or review the route."
        )

        if contract_result is not None:

            result[
                "contract_recommendation"
            ] = "DO NOT CHARTER"

            result[
                "contract_type"
            ] = "NONE"

    return result


def main():

    print(
        "\nFreightWise Decision Pipeline"
    )

    print(
        "=" * 40
    )

    # =========================================================
    # TEST VESSEL CANDIDATES
    # =========================================================
    #
    # These are SYNTHETIC TEST FIXTURES.
    # They are NOT verified commercial vessel data.
    #
    # Replace them with actual vessel data when available.
    # =========================================================

    vessel_candidates = [

        VesselCandidate(
            vessel_name="Handysize Candidate",
            vessel_type="Handysize",
            dwt_tons=40000,
            loa_m=180,
            beam_m=30,
            draft_m=11,
        ),

        VesselCandidate(
            vessel_name="Supramax Candidate",
            vessel_type="Supramax",
            dwt_tons=60000,
            loa_m=200,
            beam_m=32,
            draft_m=12,
        ),

        VesselCandidate(
            vessel_name="Panamax Candidate",
            vessel_type="Panamax",
            dwt_tons=75000,
            loa_m=225,
            beam_m=32,
            draft_m=13,
        ),

        VesselCandidate(
            vessel_name="Capesize Candidate",
            vessel_type="Capesize",
            dwt_tons=180000,
            loa_m=290,
            beam_m=45,
            draft_m=17,
        ),
    ]

    # ---------------------------------------------------------
    # Backward-compatible default vessel.
    #
    # The optimizer will select the best feasible candidate.
    # ---------------------------------------------------------

    vessel = VesselInput(
        vessel_name="Example Vessel",
        vessel_type="Panamax",
        dwt_tons=75000,
        loa_m=225,
        beam_m=32,
        draft_m=13,
    )

    # =========================================================
    # SYNTHETIC COMMERCIAL INPUTS FOR TESTING ONLY
    # =========================================================

    commercial_input = ContractInput(
        current_spot_rate_usd_day=10000,
        contract_rate_usd_day=8500,
        expected_future_spot_rate_usd_day=10500,
        voyages=6,
        voyage_days=30,
        contract_months=6,
        risk_score=40,
    )

    # =========================================================
    # RUN PIPELINE
    # =========================================================

    result = run_decision_pipeline(
        vessel=vessel,
        port_name="Paradip Port",
        commercial_input=commercial_input,
        vessel_candidates=vessel_candidates,
    )

    output = pd.DataFrame(
        [result]
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # =========================================================
    # PRINT RESULTS
    # =========================================================

    print(
        "\nPipeline completed."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        "\nDecision date:"
    )

    print(
        result[
            "decision_date"
        ]
    )

    print(
        "\nRecommended Vessel Type:"
    )

    print(
        result[
            "recommended_vessel_type"
        ]
    )

    print(
        "\nRecommended Vessel:"
    )

    print(
        result[
            "recommended_vessel_name"
        ]
    )

    print(
        "\nVessel Suitability Score:"
    )

    print(
        result[
            "recommended_vessel_suitability_score"
        ]
    )

    print(
        "\nFinal Recommendation:"
    )

    print(
        result[
            "final_recommendation"
        ]
    )

    print(
        "\nFinal Reason:"
    )

    print(
        result[
            "final_reason"
        ]
    )

    print(
        "\nMarket Entry Signal:"
    )

    print(
        result[
            "market_entry_signal"
        ]
    )

    print(
        "\nForecast Used:"
    )

    print(
        result[
            "forecast_freight_usd_day"
        ]
    )

    print(
        "\nContract Future Spot Used:"
    )

    print(
        result.get(
            "expected_future_spot_rate_usd_day"
        )
    )

    print(
        "\nContract Recommendation:"
    )

    print(
        result.get(
            "contract_recommendation"
        )
    )

    print(
        "\nContract Type:"
    )

    print(
        result.get(
            "contract_type"
        )
    )

    print(
        "\nPort Feasibility:"
    )

    print(
        result[
            "port_feasibility"
        ]
    )

    print(
        "\nFeasibility Score:"
    )

    print(
        result[
            "feasibility_score"
        ]
    )

    print(
        "\nRisk Data Available:"
    )

    print(
        result[
            "risk_data_available"
        ]
    )

    print(
        "\nFull Result:"
    )

    print(
        output.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()