import React from "react";
import { Play } from "lucide-react";
import Card from "../../components/common/Card";
import SectionTitle from "../../components/common/SectionTitle";
import Field from "../../components/common/Field";
import Page from "../../components/layout/Page";

const rows = [
  ["Recommended", "MV Ocean Pride", "Dampier → Paradip", "$1.84M", "Low", "20 Sep"],
  ["Cheapest", "MV Frontier", "Dampier → Paradip", "$1.96M", "Medium", "24 Sep"],
  ["Fastest", "MV Blue Horizon", "Dampier → Vizag", "$2.04M", "Low", "18 Sep"],
  ["Lowest Risk", "MV Unity", "Newcastle → Paradip", "$1.92M", "Low", "22 Sep"],
];

export default function Simulation({ go }) {
  return (
    <Page title="Simulation" subtitle="Compare scenarios to evaluate cost, risk and delivery time.">
      <div className="fw-two-col">
        <Card>
          <SectionTitle title="Scenario Inputs" />
          <Field label="Vessel Class" value="Capesize" />
          <Field label="Alternative Loading Port" />
          <Field label="Alternative Discharge Port" />
          <Field label="Charter Start Date" />
          <button type="button" className="fw-primary fw-full" onClick={() => go("analysis")}>
            <Play size={15} />
            Run Simulation
          </button>
        </Card>

        <Card>
          <SectionTitle title="Scenario Comparison" />
          <div className="fw-scenario fw-scenario-head">
            <b>Option</b>
            <b>Vessel</b>
            <b>Port Route</b>
            <b>Total Cost</b>
            <b>Risk</b>
            <b>Arrival</b>
          </div>
          {rows.map((row) => (
            <div className="fw-scenario" key={row[0]}>
              {row.map((value, index) => <span key={index}>{value}</span>)}
            </div>
          ))}
        </Card>
      </div>

      <Card>
        <SectionTitle title="Key Takeaway" />
        <p>The recommended option offers the best balance of cost, risk and delivery time.</p>
      </Card>
    </Page>
  );
}
