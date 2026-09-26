import React, { useEffect, useState } from "react";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import SectionTitle from "../../components/common/SectionTitle";
import Cost from "../../components/common/Cost";
import Risk from "../../components/common/Risk";
import Page from "../../components/layout/Page";
import { getVessels, getPorts } from "../../services/api";

export default function Analysis({ go, recommendation }) {
  const [vessels, setVessels] = useState([]);
  const [ports, setPorts] = useState([]);

  useEffect(() => {
    getVessels()
      .then((data) => setVessels(data.vessels || []))
      .catch((error) => {
        console.error("Failed to load vessels:", error);
      });

    getPorts()
      .then((data) => setPorts(data.ports || []))
      .catch((error) => {
        console.error("Failed to load ports:", error);
      });
  }, []);

  const recommendedVessel = vessels.find(
    (vessel) => vessel.id === recommendation?.vessel_id
  );

  const recommendedPort = ports.find(
    (port) => port.id === recommendation?.port_id
  );

  const alternatives = recommendation?.alternatives || [];

  return (
    <Page
      title="Voyage Analysis"
      subtitle="AI-powered recommendation based on your voyage inputs."
    >
      <div className="fw-analysis-top">
        <Card className="fw-score-card">
          <div className="fw-eyebrow">OVERALL RECOMMENDATION</div>

          <Badge tone="teal">RECOMMENDED</Badge>

          <div className="fw-score">
            {recommendation?.score != null
              ? Number(recommendation.score).toFixed(2)
              : "N/A"}
            <span>/100</span>
          </div>

          <p>
            {recommendation?.reasons?.[0] ||
              "Recommendation based on your voyage requirements."}
          </p>
        </Card>

        <Card>
          <div className="fw-eyebrow">RECOMMENDED VESSEL</div>

          <h3>{recommendedVessel?.name || "Loading vessel..."}</h3>

          {recommendedVessel && (
            <p>
              {recommendedVessel.vessel_class} ·{" "}
              {Number(recommendedVessel.dwt).toLocaleString()} DWT · LOA{" "}
              {recommendedVessel.loa_m} m
            </p>
          )}

          <button
            type="button"
            className="fw-secondary"
            onClick={() => go("vessels")}
          >
            View Vessel Details
          </button>
        </Card>

        <Card>
          <div className="fw-eyebrow">RECOMMENDED PORT PLAN</div>

          <h3>{recommendedPort?.name || "Loading port..."}</h3>

          {recommendedPort && (
            <p>
              {recommendedPort.code} · {recommendedPort.state},{" "}
              {recommendedPort.country}
            </p>
          )}

          <button
            type="button"
            className="fw-secondary"
            onClick={() => go("ports")}
          >
            View Port Details
          </button>
        </Card>

        <Card>
          <div className="fw-eyebrow">RECOMMENDED CHARTER WINDOW</div>

          <h3>
            {recommendation?.forecast?.forecast_date || "N/A"}
          </h3>

          <p>
            Required arrival date:{" "}
            {recommendation?.forecast?.forecast_date || "N/A"}
          </p>

          <Badge tone="teal">ON TIME</Badge>
        </Card>
      </div>

      <div className="fw-two-col">
        <Card>
          <SectionTitle title="Cost Analysis" />

          <Cost
            label="Freight Cost"
            value={
              recommendation?.cost?.freight_cost != null
                ? `$${Number(
                    recommendation.cost.freight_cost
                  ).toLocaleString()}`
                : "$0"
            }
          />

          <Cost
            label="Bunker Cost"
            value={
              recommendation?.cost?.bunker_cost != null
                ? `$${Number(
                    recommendation.cost.bunker_cost
                  ).toLocaleString()}`
                : "$0"
            }
          />

          <Cost
            label="Port Cost"
            value={
              recommendation?.cost?.port_cost != null
                ? `$${Number(
                    recommendation.cost.port_cost
                  ).toLocaleString()}`
                : "$0"
            }
          />

          <Cost
            label="Demurrage (Est.)"
            value={
              recommendation?.cost?.expected_demurrage != null
                ? `$${Number(
                    recommendation.cost.expected_demurrage
                  ).toLocaleString()}`
                : "N/A"
            }
          />

          <hr />

          <Cost
            label="Total Landed Cost"
            value={
              recommendation?.cost?.total_landed_cost != null
                ? `$${Number(
                    recommendation.cost.total_landed_cost
                  ).toLocaleString()}`
                : "$0"
            }
            strong
          />
        </Card>

        <Card>
          <SectionTitle title="Risk Assessment" />

          <Risk
            label="Overall Risk"
            value={recommendation?.risk?.risk_level || "N/A"}
          />

          <Risk
            label="Delay Risk"
            value={
              recommendation?.alternatives?.[0]
                ?.expected_delay_hours != null
                ? `${recommendation.alternatives[0].expected_delay_hours} hrs`
                : "UNKNOWN"
            }
          />

          <Risk
            label="Port Congestion"
            value={
              recommendation?.risk?.factors?.congestion?.impact ||
              "UNKNOWN"
            }
          />

          <Risk
            label="Weather Risk"
            value={
              recommendation?.risk?.factors?.weather?.impact ||
              "UNKNOWN"
            }
          />

          <Risk
            label="Freight Price Risk"
            value={
              recommendation?.forecast?.data_status ||
              "UNKNOWN"
            }
          />
        </Card>
      </div>

      <Card>
        <SectionTitle title="Why This Recommendation?" />

        <ol className="fw-reasons">
          {recommendation?.reasons?.length ? (
            recommendation.reasons.map((reason, index) => (
              <li key={index}>{reason}</li>
            ))
          ) : (
            <li>No recommendation reasons available.</li>
          )}
        </ol>
      </Card>

      <Card>
        <SectionTitle
          title="Alternative Options"
          right={
            <button
              type="button"
              className="fw-secondary"
              onClick={() => go("simulation")}
            >
              Compare in Simulation
            </button>
          }
        />

        {alternatives.length ? (
          alternatives.map((alternative) => {
            const vessel = vessels.find(
              (item) => item.id === alternative.vessel_id
            );

            return (
              <div className="fw-alt-row" key={alternative.rank}>
                <b>Rank {alternative.rank}</b>

                <span>
                  {vessel?.name || `Vessel ID: ${alternative.vessel_id}`}
                </span>

                <span>
                  $
                  {Number(
                    alternative.total_landed_cost
                  ).toLocaleString()}
                </span>

                <span>
                  Risk: {alternative.overall_risk}
                </span>
              </div>
            );
          })
        ) : (
          <div className="fw-alt-row">
            <span>No alternatives available.</span>
          </div>
        )}
      </Card>
    </Page>
  );
}