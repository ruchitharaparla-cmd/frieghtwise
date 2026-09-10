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

export default function RiskScore() {
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
          value="24%"
          label="Low"
          progress={24}
          type="green"
        />

        <RiskGauge
          title="Port Congestion"
          value="41%"
          label="Moderate"
          progress={41}
          type="orange"
        />

        <RiskGauge
          title="Vessel Availability"
          value="18%"
          label="Low"
          progress={18}
          type="green"
        />
      </div>
    </section>
  );
}