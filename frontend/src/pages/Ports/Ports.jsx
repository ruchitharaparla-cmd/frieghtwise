import React, { useEffect, useState } from "react";
import { Search } from "lucide-react";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import Page from "../../components/layout/Page";
import { getPorts } from "../../services/api";

export default function Ports({ go }) {
  const [ports, setPorts] = useState([]);
  const [search, setSearch] = useState("");
  const [country, setCountry] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPorts()
      .then((data) => {
        setPorts(data.ports || []);
      })
      .catch((error) => {
        console.error("Failed to load ports:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const filteredPorts = ports.filter((port) => {
    const searchMatch =
      port.name.toLowerCase().includes(search.toLowerCase()) ||
      port.code.toLowerCase().includes(search.toLowerCase());

    const countryMatch =
      country === "all" || port.country === country;

    return searchMatch && countryMatch;
  });

  return (
    <Page
      title="Ports"
      subtitle="Explore port capabilities and operational status."
    >
      <Card>
        <div className="fw-directory-head">
          <div className="fw-search inline">
            <Search size={15} />
            <input
              type="text"
              placeholder="Search port name, code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          >
            <option value="all">All Countries</option>

            {[...new Set(ports.map((port) => port.country))].map(
              (item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              )
            )}
          </select>
        </div>

        <div className="fw-port-image">
          <img
            src="/assets/port-terminal.png"
            alt="Port terminal"
          />
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
              {loading ? (
                <tr>
                  <td colSpan="8">Loading ports...</td>
                </tr>
              ) : filteredPorts.length === 0 ? (
                <tr>
                  <td colSpan="8">No ports found.</td>
                </tr>
              ) : (
                filteredPorts.map((port, index) => {
                  const status =
                    port.average_waiting_hours != null &&
                    port.average_waiting_hours > 20
                      ? "Congested"
                      : "Operational";

                  return (
                    <tr key={port.id}>
                      <td>{index + 1}</td>

                      <td>
                        <b>{port.name}</b>
                      </td>

                      <td>{port.code}</td>

                      <td>{port.state}</td>

                      <td>
                        {port.max_draft_m != null
                          ? `${port.max_draft_m} m`
                          : "N/A"}
                      </td>

                      <td>
                        {port.average_waiting_hours != null
                          ? `${port.average_waiting_hours} h`
                          : "N/A"}
                      </td>

                      <td>
                        <Badge
                          tone={
                            status === "Operational"
                              ? "teal"
                              : "sand"
                          }
                        >
                          {status}
                        </Badge>
                      </td>

                      <td>
                        <button
                          type="button"
                          className="fw-link"
                          onClick={() => go("new-voyage")}
                        >
                          Use as Destination
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </Page>
  );
}