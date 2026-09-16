import React, { useState } from "react";
import { Search, Ship, ArrowUpRight } from "lucide-react";

import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import PageContainer from "../../components/common/PageContainer";

const vessels = [
  {
    name: "MV Eastern Star",
    type: "Capesize",
    dwt: "180,000",
    loa: "292 m",
    draft: "18.2 m",
    cargo: "Iron Ore, Coal",
    status: "Available",
  },
  {
    name: "MV Ocean Pioneer",
    type: "Panamax",
    dwt: "82,000",
    loa: "229 m",
    draft: "14.1 m",
    cargo: "Coal, Grain",
    status: "Available",
  },
  {
    name: "MV Blue Horizon",
    type: "Supramax",
    dwt: "58,000",
    loa: "190 m",
    draft: "12.4 m",
    cargo: "Bulk Cargo",
    status: "Under review",
  },
  {
    name: "MV Coastal Trader",
    type: "Handysize",
    dwt: "35,000",
    loa: "175 m",
    draft: "10.2 m",
    cargo: "Grain, Steel",
    status: "Available",
  },
];

export default function Vessels({ go }) {
  const [search, setSearch] = useState("");

  const filteredVessels = vessels.filter((vessel) => {
    const query = search.toLowerCase();

    return (
      vessel.name.toLowerCase().includes(query) ||
      vessel.type.toLowerCase().includes(query) ||
      vessel.cargo.toLowerCase().includes(query)
    );
  });

  return (
    <PageContainer
      title="Vessels"
      subtitle="Explore available vessels and match them with your voyage requirements."
    >
      <Card>
        <div className="fw-toolbar">
          <div>
            <h3>Vessel fleet</h3>
            <p>Available and registered vessels</p>
          </div>

          <div className="fw-search">
            <Search size={17} />
            <input
              type="text"
              placeholder="Search vessels..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </div>

        <div className="fw-table-wrapper">
          <table className="fw-table">
            <thead>
              <tr>
                <th>Vessel</th>
                <th>Class</th>
                <th>DWT</th>
                <th>LOA</th>
                <th>Draft</th>
                <th>Cargo types</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {filteredVessels.map((vessel) => (
                <tr key={vessel.name}>
                  <td>
                    <div className="fw-table-vessel">
                      <div className="fw-table-icon">
                        <Ship size={18} />
                      </div>

                      <strong>{vessel.name}</strong>
                    </div>
                  </td>

                  <td>{vessel.type}</td>
                  <td>{vessel.dwt}</td>
                  <td>{vessel.loa}</td>
                  <td>{vessel.draft}</td>
                  <td>{vessel.cargo}</td>

                  <td>
                    <Badge
                      tone={
                        vessel.status === "Available" ? "teal" : "orange"
                      }
                    >
                      {vessel.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredVessels.length === 0 && (
          <div className="fw-empty-state">
            No vessels found for your search.
          </div>
        )}
      </Card>

      <Card>
        <div className="fw-section-title">
          <h3>Need a vessel recommendation?</h3>

          <button
            type="button"
            className="fw-text-btn"
            onClick={() => go("new-voyage")}
          >
            Create voyage
            <ArrowUpRight size={15} />
          </button>
        </div>

        <p className="fw-muted">
          Enter your cargo, route, and delivery requirements to receive an
          AI-powered vessel recommendation.
        </p>
      </Card>
    </PageContainer>
  );
}