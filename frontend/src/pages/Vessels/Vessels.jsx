import React from "react";
import { Search } from "lucide-react";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import Page from "../../components/layout/Page";

const rows = [
  ["MV Ocean Pride", "Capesize", "180,000", "292", "Available"],
  ["MV Blue Horizon", "Panamax", "82,000", "229", "Available"],
  ["MV Sea Crown", "Supramax", "58,000", "190", "In Transit"],
  ["MV Eastern Star", "Handysize", "37,000", "180", "Available"],
  ["MV Unity", "Panamax", "76,000", "225", "Available"],
];

export default function Vessels({ go }) {
  return (
    <Page title="Vessels" subtitle="Explore available vessels and their specifications.">
      <Card>
        <div className="fw-directory-head">
          <div className="fw-search inline">
            <Search size={15} />
            Search vessel name, class...
          </div>
          <select defaultValue="all">
            <option value="all">All Vessel Classes</option>
          </select>
        </div>

        <div className="fw-feature-image">
          <img src="/assets/cargo-vessel.png" alt="Cargo vessel" />
        </div>

        <div className="fw-table-wrapper">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Vessel</th>
                <th>Class</th>
                <th>DWT</th>
                <th>LOA (m)</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={row[0]}>
                  <td>{index + 1}</td>
                  <td><b>{row[0]}</b></td>
                  <td>{row[1]}</td>
                  <td>{row[2]}</td>
                  <td>{row[3]}</td>
                  <td>
                    <Badge tone={row[4] === "Available" ? "teal" : "sand"}>
                      {row[4]}
                    </Badge>
                  </td>
                  <td>
                    <button type="button" className="fw-link" onClick={() => go("new-voyage")}>
                      Use in Voyage
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </Page>
  );
}
