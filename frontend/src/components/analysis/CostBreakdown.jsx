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

export default function CostBreakdown({ data }) {
  const value = (v) =>
    typeof v === "number" ? `USD ${v.toLocaleString()}` : "Unavailable";

  const total = data?.total_landed_cost;
  const freight = data?.freight_cost;
  const bunker = data?.bunker_cost;
  const port = data?.port_cost;
  const delay = data?.expected_delay_cost;
  const demurrage = data?.expected_demurrage;

  const percent = (v) =>
    typeof v === "number" && typeof total === "number" && total > 0
      ? `${Math.round((v / total) * 100)}%`
      : "N/A";
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
              <strong>{value(total)}</strong>
              <span>Total Expected Cost</span>
            </div>
          </div>
        </div>

        <div className="cost-list">
          <CostRow
            color="blue"
            name="Base Freight"
            value={value(freight)}
            percent={percent(freight)}
          />

          <CostRow
            color="orange"
            name="Bunker / Fuel"
            value={value(bunker)}
            percent={percent(bunker)}
          />

          <CostRow
            color="purple"
            name="Port Charges"
            value={value(port)}
            percent={percent(port)}
          />

          <CostRow
            color="dark-blue"
            name="Expected Demurrage"
            value={value(demurrage)}
            percent={percent(demurrage)}
          />

          <CostRow
            color="light-blue"
            name="Other Costs"
            value={value(delay)}
            percent={percent(delay)}
          />
        </div>

        <div className="hidden-risk">
          <strong>Expected Additional Costs</strong>

          <span>{typeof delay === "number" ? value(delay) : "Unavailable"}</span>

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