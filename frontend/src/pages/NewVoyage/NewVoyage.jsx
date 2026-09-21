import React from "react";
import { ChevronRight } from "lucide-react";
import Card from "../../components/common/Card";
import Field from "../../components/common/Field";
import Step from "../../components/common/Step";
import Page from "../../components/layout/Page";

export default function NewVoyage({ go }) {
  return (
    <Page
      title="New Voyage"
      subtitle="Enter voyage requirements to get AI-powered recommendations."
    >
      <Card>
        <Step number="1" title="Cargo Details">
          <Field label="Voyage Name" placeholder="Australia Coal Import — Sep 2026" />
          <Field label="Cargo Type" value="Coal" />
          <Field label="Cargo Quantity (MT)" value="75000" />
        </Step>

        <Step number="2" title="Route Details">
          <Field label="Origin Country" value="Australia" />
          <Field label="Destination Region" value="East Coast India" />
          <Field label="Loading Port (Optional)" />
          <Field label="Discharge Port (Optional)" />
        </Step>

        <Step number="3" title="Delivery Requirement">
          <Field label="Required Arrival Date" value="20 Sep 2026" />
          <Field label="Latest Acceptable Arrival" />
          <Field label="Flexibility" value="Normal" />
        </Step>

        <div className="fw-actions">
          <button type="button" className="fw-primary" onClick={() => go("analysis")}>
            Find Best Vessel, Port & Charter Time
            <ChevronRight size={16} />
          </button>
        </div>
      </Card>
    </Page>
  );
}
