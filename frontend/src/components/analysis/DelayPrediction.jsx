import React from "react";

export default function DelayPrediction({ data }) {
  const congestion = data?.factors?.congestion?.score;

  const delayHours =
    typeof data?.expected_delay_hours === "number"
      ? data.expected_delay_hours
      : typeof congestion === "number"
      ? congestion
      : null;

  const demurrage = data?.factors?.demurrage?.impact;

  const formatDelay = (hours) =>
    typeof hours === "number"
      ? `${(hours / 24).toFixed(1)} Days`
      : "Unavailable";
  return (
    <section className="panel delay-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">◷</span>
          Delay Prediction
        </div>
      </div>

      <div className="delay-item">
        <div className="delay-icon blue-bg">◴</div>

        <div>
          <span>Expected Delay</span>
          <strong>{formatDelay(delayHours)}</strong>
          <small>Backend estimate</small>
        </div>
      </div>

      <div className="delay-item">
        <div className="delay-icon orange-bg">₹</div>

        <div>
          <span>Expected Demurrage</span>
          <strong>{typeof demurrage === "number" ? `Score ${demurrage}` : "Unavailable"}</strong>
          <small>Risk factor</small>
        </div>
      </div>
    </section>
  );
}