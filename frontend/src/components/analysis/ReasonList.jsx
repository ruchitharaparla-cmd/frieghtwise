import React from "react";

export default function ReasonList({ reasons = [] }) {
  const displayReasons =
    reasons.length > 0
      ? reasons
      : ["No recommendation reasons are currently available."];

  return (
    <section className="panel why-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">💡</span>
          Why this recommendation?
        </div>
      </div>

      <div className="reason-list">
        {displayReasons.map((reason) => (
          <div className="reason" key={reason}>
            <span>✓</span>
            <p>{reason}</p>
          </div>
        ))}
      </div>
    </section>
  );
}