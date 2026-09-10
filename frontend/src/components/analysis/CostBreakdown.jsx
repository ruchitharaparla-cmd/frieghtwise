import React from "react";

function CostRow({ color, name, value, percent }) {
  return (
    <div className="cost-row">
      <span className={`cost-dot ${color}`} />
      <span className="cost-name">{name}</span>
      <strong>{value}</strong>
      <small>({percent})</small>
    </div>
  );
}

export default function CostBreakdown() {
  return (
    <section className="panel cost-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">▣</span>
          True Voyage Cost Breakdown
        </div>
      </div>

      <div className="cost-content">
        <div className="donut-wrapper">
          <div className="donut">
            <div className="donut-center">
              <strong>₹ 6.42 Cr</strong>
              <span>Total Expected Cost</span>
            </div>
          </div>
        </div>

        <div className="cost-list">
          <CostRow
            color="blue"
            name="Base Freight"
            value="₹ 4.10 Cr"
            percent="64%"
          />

          <CostRow
            color="orange"
            name="Bunker / Fuel"
            value="₹ 0.82 Cr"
            percent="13%"
          />

          <CostRow
            color="purple"
            name="Port Charges"
            value="₹ 0.46 Cr"
            percent="7%"
          />

          <CostRow
            color="dark-blue"
            name="Expected Demurrage"
            value="₹ 0.36 Cr"
            percent="6%"
          />

          <CostRow
            color="light-blue"
            name="Other Costs"
            value="₹ 0.46 Cr"
            percent="7%"
          />
        </div>

        <div className="hidden-risk">
          <strong>Hidden Cost Risk</strong>

          <span>+8.4%</span>

          <p>
            Due to potential delays,
            weather and port
            congestion.
          </p>
        </div>
      </div>

      <div className="cost-warning">
        <span>!</span>
        Actual costs may vary based on real-time port conditions,
        fuel prices and weather changes.
      </div>
    </section>
  );
}