import React from "react";

function Kpi({ icon, title, value, subtitle, type }) {
  return (
    <div className="kpi-card">
      <div className={`kpi-icon ${type}`}>
        {icon}
      </div>

      <div>
        <span className="kpi-title">{title}</span>

        <strong className="kpi-value">{value}</strong>

        {subtitle && (
          <span className="kpi-subtitle">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}

export default function RecommendationCard({ data, voyage }) {
  const vesselName =
    data?.vessel_name ||
    (data?.vessel_id ? `Vessel #${data.vessel_id}` : "Vessel unavailable");

  const portName =
    data?.port_name ||
    (data?.port_id ? `Port #${data.port_id}` : "Port unavailable");

  const strategy = data?.strategy || "Recommendation unavailable";

  const totalCost = data?.cost?.total_landed_cost;
  const riskScore = data?.risk?.overall_risk;
  const riskLevel = data?.risk?.risk_level;
  const delayHours = data?.risk?.factors?.congestion?.score;

  const formatCost = (value) =>
    typeof value === "number"
      ? `USD ${value.toLocaleString()}`
      : "Unavailable";

  const formatRisk = (value) =>
    typeof value === "number" ? `${value} / 100` : "Unavailable";

  const formatDelay = (value) =>
    typeof value === "number"
      ? `${(value / 24).toFixed(1)} Days`
      : "Unavailable";
  return (
    <section className="recommendation-card">
      <div className="recommendation-main">
        <div className="recommendation-image">
          <div className="ship-photo">
            🚢
          </div>

          <div className="recommendation-vessel">
            <strong>{vesselName}</strong>
            <span>
              {voyage?.vesselType || "Vessel selected by backend"}
            </span>
          </div>
        </div>

        <div className="recommendation-copy">
          <div className="recommendation-label">
            ✓ &nbsp; FREIGHTWISE RECOMMENDS
          </div>

          <h2>
            {strategy}
            <br />
            {portName}
          </h2>

          <p>
            Best option calculated from freight, cost, risk and feasibility.
          </p>
        </div>

        <div className="confidence-box">
          <strong>
              {data?.forecast?.confidence != null
                ? `${Math.round(Number(data.forecast.confidence) * 100)}%`
                : "N/A"}
            </strong>
          <span>Confidence</span>

          <div className="confidence-bar">
            <div
                style={{
                  width:
                    data?.forecast?.confidence != null
                      ? `${Math.round(Number(data.forecast.confidence) * 100)}%`
                      : "0%",
                }}
              />
          </div>
        </div>
      </div>

      <div className="kpi-row">
        <Kpi
          icon="▣"
          title="Expected Total Cost"
          value={formatCost(totalCost)}
          type="blue"
        />

        <Kpi
          icon="↗"
          title="Expected Savings"
          value="Unavailable"
          subtitle="vs. current market"
          type="green"
        />

        <Kpi
          icon="✓"
          title="Risk Score"
          value={formatRisk(riskScore)}
          subtitle={riskLevel || "Unavailable"}
          type="green"
        />

        <Kpi
          icon="◷"
          title="Expected Delay"
          value={formatDelay(delayHours)}
          type="blue"
        />
      </div>
    </section>
  );
}