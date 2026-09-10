import React from "react";

export default function ReasonList() {
  const reasons = [
    "Freight rate expected to decrease moderately",
    "Vessel matches cargo requirement",
    "Paradip has acceptable draft and port infrastructure",
    "Lower congestion compared to alternative ports",
    "Low weather risk during the booking window",
    "Lower expected demurrage",
    "Better overall voyage cost and availability",
  ];

  return (
    <section className="panel why-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">💡</span>
          Why this recommendation?
        </div>
      </div>

      <div className="reason-list">
        {reasons.map((reason) => (
          <div className="reason" key={reason}>
            <span>✓</span>
            <p>{reason}</p>
          </div>
        ))}
      </div>
    </section>
  );
}