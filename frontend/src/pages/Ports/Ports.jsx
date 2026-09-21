import React from "react";
import { Search } from "lucide-react";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import Page from "../../components/layout/Page";

const rows = [
  ["Paradip Port", "INPRP", "Odisha", "16.0", "28", "Operational"],
  ["Vizag Port", "INVTZ", "Andhra Pradesh", "16.5", "36", "Operational"],
  ["Gangavaram Port", "INGWV", "Andhra Pradesh", "18.0", "42", "Congested"],
  ["Kakinada Port", "INKAK", "Andhra Pradesh", "16.0", "30", "Operational"],
  ["Chennai Port", "INMAA", "Tamil Nadu", "14.5", "26", "Operational"],
];

export default function Ports({ go }) {
  return (
    <Page title="Ports" subtitle="Explore port capabilities and operational status.">
      <Card>
        <div className="fw-directory-head">
          <div className="fw-search inline">
            <Search size={15} />
            Search port name, code...
          </div>
          <select defaultValue="all">
            <option value="all">All Countries</option>
          </select>
        </div>

        <div className="fw-port-image">
          <img src="/assets/port-terminal.png" alt="Port terminal" />
        </div>

        <div className="fw-table-wrapper">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Port Name</th>
                <th>Code</th>
                <th>State</th>
                <th>Max Draft</th>
                <th>Avg Waiting</th>
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
                  <td>{row[3]} m</td>
                  <td>{row[4]} h</td>
                  <td>
                    <Badge tone={row[5] === "Operational" ? "teal" : "sand"}>
                      {row[5]}
                    </Badge>
                  </td>
                  <td>
                    <button type="button" className="fw-link" onClick={() => go("new-voyage")}>
                      Use as Destination
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
