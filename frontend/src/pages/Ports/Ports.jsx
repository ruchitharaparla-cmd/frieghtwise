import React, { useState } from "react";
import { Search, Anchor, ArrowUpRight } from "lucide-react";

import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import PageContainer from "../../components/common/PageContainer";

const ports = [
  {
    name: "Visakhapatnam",
    code: "INVTZ",
    state: "Andhra Pradesh",
    draft: "18.5 m",
    loa: "300 m",
    utilization: "78%",
    waiting: "16 hrs",
    status: "Operational",
  },
  {
    name: "Gangavaram",
    code: "INGGV",
    state: "Andhra Pradesh",
    draft: "20.0 m",
    loa: "320 m",
    utilization: "72%",
    waiting: "12 hrs",
    status: "Operational",
  },
  {
    name: "Kakinada",
    code: "INKAK",
    state: "Andhra Pradesh",
    draft: "14.5 m",
    loa: "250 m",
    utilization: "64%",
    waiting: "20 hrs",
    status: "Operational",
  },
  {
    name: "Paradip",
    code: "INPRT",
    state: "Odisha",
    draft: "18.7 m",
    loa: "310 m",
    utilization: "81%",
    waiting: "22 hrs",
    status: "Busy",
  },
  {
    name: "Kamarajar",
    code: "INENN",
    state: "Tamil Nadu",
    draft: "16.5 m",
    loa: "280 m",
    utilization: "69%",
    waiting: "14 hrs",
    status: "Operational",
  },
];

export default function Ports({ go }) {
  const [search, setSearch] = useState("");

  const filteredPorts = ports.filter((port) => {
    const query = search.toLowerCase();

    return (
      port.name.toLowerCase().includes(query) ||
      port.code.toLowerCase().includes(query) ||
      port.state.toLowerCase().includes(query)
    );
  });

  return (
    <PageContainer
      title="Ports"
      subtitle="Review port restrictions, capacity, utilization, and waiting times."
    >
      <Card>
        <div className="fw-toolbar">
          <div>
            <h3>East Coast ports</h3>
            <p>Port infrastructure and operational conditions</p>
          </div>

          <div className="fw-search">
            <Search size={17} />
            <input
              type="text"
              placeholder="Search ports..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </div>

        <div className="fw-table-wrapper">
          <table className="fw-table">
            <thead>
              <tr>
                <th>Port</th>
                <th>Code</th>
                <th>State</th>
                <th>Max draft</th>
                <th>Max LOA</th>
                <th>Utilization</th>
                <th>Waiting time</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {filteredPorts.map((port) => (
                <tr key={port.code}>
                  <td>
                    <div className="fw-table-vessel">
                      <div className="fw-table-icon">
                        <Anchor size={18} />
                      </div>

                      <strong>{port.name}</strong>
                    </div>
                  </td>

                  <td>{port.code}</td>
                  <td>{port.state}</td>
                  <td>{port.draft}</td>
                  <td>{port.loa}</td>
                  <td>{port.utilization}</td>
                  <td>{port.waiting}</td>

                  <td>
                    <Badge tone={port.status === "Busy" ? "orange" : "teal"}>
                      {port.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredPorts.length === 0 && (
          <div className="fw-empty-state">
            No ports found for your search.
          </div>
        )}
      </Card>

      <Card>
        <div className="fw-section-title">
          <h3>Plan your next voyage</h3>

          <button
            type="button"
            className="fw-text-btn"
            onClick={() => go("new-voyage")}
          >
            Start planning
            <ArrowUpRight size={15} />
          </button>
        </div>

        <p className="fw-muted">
          Select suitable loading and discharge ports based on vessel
          restrictions, cargo type, and expected waiting time.
        </p>
      </Card>
    </PageContainer>
  );
}