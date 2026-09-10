import React from "react";

export default function DelayPrediction() {
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
          <strong>2.4 Days</strong>
          <small>(± 1.1 days)</small>
        </div>
      </div>

      <div className="delay-item">
        <div className="delay-icon orange-bg">₹</div>

        <div>
          <span>Expected Demurrage</span>
          <strong>₹ 28.4 Lakhs</strong>
          <small>(± 12.6)</small>
        </div>
      </div>
    </section>
  );
}