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

export default function RecommendationCard() {
  return (
    <section className="recommendation-card">
      <div className="recommendation-main">
        <div className="recommendation-image">
          <div className="ship-photo">
            🚢
          </div>

          <div className="recommendation-vessel">
            <strong>MV Ocean Star</strong>
            <span>
              76,000 DWT&nbsp; | &nbsp;Bulk Carrier
            </span>
          </div>
        </div>

        <div className="recommendation-copy">
          <div className="recommendation-label">
            ✓ &nbsp; FREIGHTWISE RECOMMENDS
          </div>

          <h2>
            Charter MV Ocean Star between
            <br />
            12 – 18 Sep via Paradip Port.
          </h2>

          <p>
            Best balance of cost, risk and availability.
          </p>
        </div>

        <div className="confidence-box">
          <strong>87%</strong>
          <span>Confidence</span>

          <div className="confidence-bar">
            <div style={{ width: "87%" }} />
          </div>
        </div>
      </div>

      <div className="kpi-row">
        <Kpi
          icon="▣"
          title="Expected Total Cost"
          value="₹ 6.42 Cr"
          type="blue"
        />

        <Kpi
          icon="↗"
          title="Expected Savings"
          value="₹ 18.4 L"
          subtitle="vs. current market"
          type="green"
        />

        <Kpi
          icon="✓"
          title="Risk Score"
          value="32 / 100"
          subtitle="Low Risk"
          type="green"
        />

        <Kpi
          icon="◷"
          title="Expected Delay"
          value="2.4 Days"
          type="blue"
        />
      </div>
    </section>
  );
}