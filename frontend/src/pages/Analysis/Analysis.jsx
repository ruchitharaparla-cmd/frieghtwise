import React from "react";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import SectionTitle from "../../components/common/SectionTitle";
import Cost from "../../components/common/Cost";
import Risk from "../../components/common/Risk";
import Page from "../../components/layout/Page";

const voyage = {
  vessel: "MV Ocean Pride",
  port: "Dampier → Paradip",
  charter: "12–16 Sep 2026",
  arrival: "20 Sep 2026",
};

export default function Analysis({ go }) {
  return (
    <Page
      title="Voyage Analysis"
      subtitle="AI-powered recommendation based on your voyage inputs."
    >
      <div className="fw-analysis-top">
        <Card className="fw-score-card">
          <div className="fw-eyebrow">OVERALL RECOMMENDATION</div>
          <Badge tone="teal">RECOMMENDED</Badge>
          <div className="fw-score">
            86<span>/100</span>
          </div>
          <p>Meets delivery deadline with lowest estimated total cost.</p>
        </Card>

        <Card>
          <div className="fw-eyebrow">RECOMMENDED VESSEL</div>
          <h3>{voyage.vessel}</h3>
          <p>Capesize · 180,000 DWT · LOA 292 m</p>
          <button type="button" className="fw-secondary" onClick={() => go("vessels")}>
            View Vessel Details
          </button>
        </Card>

        <Card>
          <div className="fw-eyebrow">RECOMMENDED PORT PLAN</div>
          <h3>{voyage.port}</h3>
          <p>Loading: Dampier · Discharge: Paradip</p>
          <button type="button" className="fw-secondary" onClick={() => go("ports")}>
            View Port Details
          </button>
        </Card>

        <Card>
          <div className="fw-eyebrow">RECOMMENDED CHARTER WINDOW</div>
          <h3>{voyage.charter}</h3>
          <p>Expected arrival: {voyage.arrival}</p>
          <Badge tone="teal">ON TIME</Badge>
        </Card>
      </div>

      <div className="fw-two-col">
        <Card>
          <SectionTitle title="Cost Analysis" />
          <Cost label="Freight Cost" value="$1,356,000" />
          <Cost label="Bunker Cost" value="$285,000" />
          <Cost label="Port Cost" value="$92,000" />
          <Cost label="Demurrage (Est.)" value="$64,500" />
          <hr />
          <Cost label="Total Landed Cost" value="$1,842,500" strong />
        </Card>

        <Card>
          <SectionTitle title="Risk Assessment" />
          <Risk label="Overall Risk" value="Low" />
          <Risk label="Delay Risk" value="Low" />
          <Risk label="Port Congestion" value="Medium" tone="sand" />
          <Risk label="Weather Risk" value="Low" />
          <Risk label="Freight Price Risk" value="Medium" tone="sand" />
        </Card>
      </div>

      <Card>
        <SectionTitle title="Why This Recommendation?" />
        <ol className="fw-reasons">
          <li>Meets the required arrival date.</li>
          <li>Lowest estimated total landed cost.</li>
          <li>Vessel capacity matches cargo quantity.</li>
          <li>Ports have acceptable waiting time.</li>
          <li>Lower delay risk compared to alternatives.</li>
        </ol>
      </Card>

      <Card>
        <SectionTitle
          title="Alternative Options"
          right={
            <button type="button" className="fw-secondary" onClick={() => go("simulation")}>
              Compare in Simulation
            </button>
          }
        />
        <div className="fw-alt-row">
          <b>Cheapest</b>
          <span>MV Frontier</span>
          <span>$1.96M</span>
          <span>Medium Risk</span>
        </div>
        <div className="fw-alt-row">
          <b>Fastest</b>
          <span>MV Blue Horizon</span>
          <span>$2.04M</span>
          <span>Low Risk</span>
        </div>
      </Card>
    </Page>
  );
}
