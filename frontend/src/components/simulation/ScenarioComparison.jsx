import React from "react";
import {
  BarChart3,
  CalendarDays,
  Clock3,
  Info,
  ShieldCheck,
} from "lucide-react";

import "./ScenarioComparison.css";
import simulImage from "../../assets/images/simul.png";

const scenarios = [
  {
    id: "now",
    title: "Charter Now",
    date: "12 – 18 Sep 2026",
    rate: "$24.8 / MT",
    cost: "₹6.42 Cr",
    risk: "Low",
    delay: "2.4 Days",
    type: "low",
    recommended: true,
    message:
      "Best balance of cost and risk for current market conditions.",
  },
  {
    id: "7",
    title: "Wait 7 Days",
    date: "19 – 25 Sep 2026",
    rate: "$23.6 / MT",
    cost: "₹6.38 Cr",
    risk: "Moderate",
    delay: "3.8 Days",
    type: "moderate",
    recommended: false,
    message:
      "Slightly lower freight rate, but higher risk of congestion and weather impact.",
  },
  {
    id: "14",
    title: "Wait 14 Days",
    date: "26 Sep – 2 Oct 2026",
    rate: "$22.5 / MT",
    cost: "₹6.71 Cr",
    risk: "High",
    delay: "5.6 Days",
    type: "high",
    recommended: false,
    message:
      "Lower freight rate but significantly higher risk and total cost due to expected delays.",
  },
];

function ScenarioCard({ scenario }) {
  return (
    <article
      className={`scenario-card scenario-${scenario.type} ${
        scenario.recommended ? "recommended-card" : ""
      }`}
    >
      {scenario.recommended && (
        <div className="recommended-badge">
          <ShieldCheck size={17} />
          <span>Recommended</span>
        </div>
      )}

      <div className="scenario-card-header">
        <div className="scenario-heading">
          <div className="scenario-main-icon">
            {scenario.id === "7" ? (
              <Clock3 size={25} />
            ) : (
              <CalendarDays size={25} />
            )}
          </div>

          <div>
            <h3>{scenario.title}</h3>
            <p>{scenario.date}</p>
          </div>
        </div>

        <img
          src={simulImage}
          alt="Cargo vessel"
          className="scenario-ship-image"
        />
      </div>

      <div className="card-divider" />

      <div className="scenario-metrics">
        <div className="metric">
          <div className="metric-icon dollar-icon">$</div>

          <div>
            <span>Freight Rate</span>
            <strong>{scenario.rate}</strong>
          </div>
        </div>

        <div className="metric">
          <div className="metric-icon">
            <BarChart3 size={19} />
          </div>

          <div>
            <span>Total Cost</span>
            <strong>{scenario.cost}</strong>
          </div>
        </div>

        <div className="metric">
          <div className="metric-icon">
            <ShieldCheck size={19} />
          </div>

          <div>
            <span>Overall Risk</span>

            <strong
              className={`risk-pill risk-${scenario.type}`}
            >
              {scenario.risk}
            </strong>
          </div>
        </div>

        <div className="metric">
          <div className="metric-icon">
            <Clock3 size={19} />
          </div>

          <div>
            <span>Expected Delay</span>
            <strong>{scenario.delay}</strong>
          </div>
        </div>
      </div>

      <div className="scenario-message">
        <ShieldCheck size={20} />
        <p>{scenario.message}</p>
      </div>
    </article>
  );
}

export default function ScenarioComparison() {
  return (
    <section className="scenario-section">
      <div className="scenario-heading-row">
        <div className="scenario-title">
          <div className="scenario-title-icon">
            <BarChart3 size={25} />
          </div>

          <div>
            <h2>Scenario Comparison</h2>
            <p>
              See how timing and market conditions impact your voyage
              cost and risk
            </p>
          </div>
        </div>

        <div className="scenario-info">
          <Info size={20} />

          <p>
            The cheapest freight rate does not always mean the lowest
            total voyage cost. Consider total cost, risk, and expected
            delays before making a decision.
          </p>
        </div>
      </div>

      <div className="scenario-grid">
        {scenarios.map((scenario) => (
          <ScenarioCard
            key={scenario.id}
            scenario={scenario}
          />
        ))}
      </div>
    </section>
  );
}