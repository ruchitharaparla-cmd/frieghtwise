import React from "react";
import { ArrowUpRight } from "lucide-react";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import Metric from "../../components/common/Metric";
import SectionTitle from "../../components/common/SectionTitle";
import Page from "../../components/layout/Page";

const voyage = {
  route: "Australia → East Coast India",
  vessel: "MV Ocean Pride",
  vesselClass: "Capesize",
  port: "Dampier → Paradip",
  charter: "12–16 Sep 2026",
  cost: "$1.84M",
  risk: "Low",
};

export default function Dashboard({ go }) {
  return (
    <Page
      title="Welcome back, Keerthi."
      subtitle="Here's your latest voyage recommendation and market overview."
    >
      <Card className="fw-hero-card">
        <img
          className="fw-hero-image"
          src="/assets/port-terminal.png"
          alt="Cargo vessel at a port during sunset"
        />
        <div className="fw-hero-overlay">
          <span>FREIGHTWISE</span>
          <h2>
            Smarter Chartering
            <br />
            for a Stronger Tomorrow
          </h2>
          <p>Better data. Lower costs. Safer voyages.</p>
        </div>
      </Card>

      <Card className="fw-recommend">
        <div className="fw-eyebrow">
          RECOMMENDED VOYAGE <Badge>RECOMMENDED</Badge>
        </div>
        <h2>{voyage.route}</h2>

        <div className="fw-metric-grid">
          <Metric label="Vessel" value={voyage.vessel} sub={voyage.vesselClass} />
          <Metric label="Port Plan" value={voyage.port} />
          <Metric label="Charter Window" value={voyage.charter} />
          <Metric label="Estimated Cost" value={voyage.cost} />
          <Metric label="Overall Risk" value={voyage.risk} />
        </div>

        <button type="button" className="fw-primary" onClick={() => go("analysis")}>
          View Full Analysis
          <ArrowUpRight size={15} />
        </button>
      </Card>

      <div className="fw-kpis">
        <Metric label="Active Voyages" value="8" />
        <Metric label="Upcoming Arrivals" value="3" />
        <Metric label="Total Freight Exposure" value="$12.4M" />
        <Metric label="Alerts" value="2" />
      </div>

      <Card>
        <SectionTitle title="Freight Rate Trend" right="Last 3 Months" />
        <div className="fw-trend">
          <div className="fw-chart">
            <svg viewBox="0 0 620 150" preserveAspectRatio="none">
              <polyline
                points="0,45 80,58 150,55 230,78 300,86 370,82 450,92"
                fill="none"
                stroke="#17324D"
                strokeWidth="3"
              />
              <polyline
                points="450,92 520,88 620,90"
                fill="none"
                stroke="#8A99A8"
                strokeWidth="3"
                strokeDasharray="7 7"
              />
              <line x1="450" y1="10" x2="450" y2="140" stroke="#D9E0E6" />
            </svg>
            <div className="fw-chart-axis">
              <span>Jun</span>
              <span>Jul</span>
              <span>Aug</span>
              <span>Sep</span>
            </div>
          </div>

          <div className="fw-rate">
            <b>$24.8 / MT</b>
            <span>Current Rate</span>
            <b>$25.6 / MT</b>
            <span>Previous Rate</span>
            <Badge tone="teal">−3.1%</Badge>
          </div>
        </div>
      </Card>
    </Page>
  );
}
