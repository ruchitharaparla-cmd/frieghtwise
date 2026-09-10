import React from "react";

function RiskGauge({
  title,
  value,
  label,
  progress,
  type,
}) {
  return (
    <div className="risk-gauge-card">
      <span>{title}</span>

      <div className={`gauge ${type}`}>
        <div
          className="gauge-progress"
          style={{
            "--progress": `${progress * 1.8}deg`,
          }}
        />
      </div>

      <strong>{value}</strong>

      <b className={type}>{label}</b>
    </div>
  );
}

export default function RiskScore({ data }) {
  const factors = data?.factors || {};

  const score = (name) =>
    typeof factors[name]?.score === "number"
      ? factors[name].score
      : null;

  const label = (value) =>
    value == null
      ? "Unavailable"
      : value < 35
      ? "Low"
      : value < 65
      ? "Moderate"
      : "High";
  return (
    <section className="panel risk-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">✓</span>
          Risk Analysis
        </div>
      </div>

      <div className="risk-grid">
        <RiskGauge
          title="Weather Risk"
          value={score("weather") != null ? `${score("weather")}%` : "Unavailable"}
          label={label(score("weather"))}
          progress={score("weather") || 0}
          type="green"
        />

        <RiskGauge
          title="Port Congestion"
          value={score("congestion") != null ? `${score("congestion")}%` : "Unavailable"}
          label={label(score("congestion"))}
          progress={score("congestion") || 0}
          type="orange"
        />

        <RiskGauge
          title="Demurrage Risk"
          value={score("demurrage") != null ? `${score("demurrage")}%` : "Unavailable"}
          label={label(score("demurrage"))}
          progress={score("demurrage") || 0}
          type={score("demurrage") != null && score("demurrage") >= 65 ? "orange" : "green"}
        />
      </div>
    </section>
  );
}