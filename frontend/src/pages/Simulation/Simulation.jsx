import React, { useState } from "react";
import { Play } from "lucide-react";
import Card from "../../components/common/Card";
import SectionTitle from "../../components/common/SectionTitle";
import Field from "../../components/common/Field";
import Page from "../../components/layout/Page";
import Badge from "../../components/common/Badge";
import { runSimulation } from "../../services/api";

export default function Simulation({ go }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const runScenario = async () => {
    setLoading(true);

    try {
      const data = await runSimulation({
        base_scenario: {
          cargo_type: "Coal",
          quantity_tonnes: 75000,
          origin_country: "Australia",
          destination_region: "East Coast India",
          arrival_date: "2026-09-20",
          charter_duration_days: 14,
        },
        changes: {
          charter_duration_days: 16,
        },
      });

      setResult(data);
    } catch (error) {
      console.error("Simulation failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const baseCost = result?.base_scenario?.total_landed_cost;
  const modifiedCost = result?.modified_scenario?.total_landed_cost;
  const costDifference = result?.differences?.cost_difference;

  return (
    <Page
      title="Simulation"
      subtitle="Compare scenarios to evaluate cost, risk and delivery time."
    >
      <div className="fw-two-col">
        <Card>
          <SectionTitle title="Scenario Inputs" />

          <Field label="Vessel Class" value="Capesize" />
          <Field label="Alternative Loading Port" />
          <Field label="Alternative Discharge Port" />
          <Field label="Charter Start Date" />

          <button
            type="button"
            className="fw-primary fw-full"
            onClick={runScenario}
            disabled={loading}
          >
            <Play size={15} />
            {loading ? "Running Simulation..." : "Run Simulation"}
          </button>
        </Card>

        <Card>
          <SectionTitle title="Scenario Comparison" />

          {!result ? (
            <div className="fw-scenario">
              <span>Run the simulation to compare scenarios.</span>
            </div>
          ) : (
            <>
              <div className="fw-scenario fw-scenario-head">
                <b>Scenario</b>
                <b>Total Cost</b>
                <b>Risk</b>
                <b>Recommendation</b>
              </div>

              <div className="fw-scenario">
                <span>Base Scenario</span>
                <span>
                  {baseCost != null
                    ? `$${Number(baseCost).toLocaleString()}`
                    : "N/A"}
                </span>
                <span>
                  {result.base_scenario?.risk?.risk_level || "N/A"}
                </span>
                <span>
                  Vessel {result.base_scenario?.recommendation?.vessel_id ??
                    "N/A"}
                </span>
              </div>

              <div className="fw-scenario">
                <span>Modified Scenario</span>
                <span>
                  {modifiedCost != null
                    ? `$${Number(modifiedCost).toLocaleString()}`
                    : "N/A"}
                </span>
                <span>
                  {result.modified_scenario?.risk?.risk_level || "N/A"}
                </span>
                <span>
                  Vessel{" "}
                  {result.modified_scenario?.recommendation?.vessel_id ??
                    "N/A"}
                </span>
              </div>
            </>
          )}
        </Card>
      </div>

      {result && (
        <Card>
          <SectionTitle title="Simulation Result" />

          <div className="fw-scenario">
            <span>Cost Difference</span>
            <b>
              {costDifference != null
                ? `$${Number(costDifference).toLocaleString()}`
                : "N/A"}
            </b>
          </div>

          <div className="fw-scenario">
            <span>Recommendation Changed</span>
            <Badge tone={result.recommendation_changed ? "sand" : "teal"}>
              {result.recommendation_changed ? "YES" : "NO"}
            </Badge>
          </div>
        </Card>
      )}

      <Card>
        <SectionTitle title="Key Takeaway" />

        {!result ? (
          <p>
            Run a simulation to compare the base voyage with the modified
            scenario.
          </p>
        ) : (
          <p>
            {result.recommendation_changed
              ? "The modified scenario changed the recommended vessel or port."
              : "The modified scenario did not change the recommendation."}
          </p>
        )}
      </Card>
    </Page>
  );
}