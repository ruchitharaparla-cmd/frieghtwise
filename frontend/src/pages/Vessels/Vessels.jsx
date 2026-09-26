import React, { useEffect, useState } from "react";
import { Search } from "lucide-react";
import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import Page from "../../components/layout/Page";
import { getVessels } from "../../services/api";

export default function Vessels({ go }) {
  const [vessels, setVessels] = useState([]);
  const [search, setSearch] = useState("");
  const [vesselClass, setVesselClass] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getVessels()
      .then((data) => setVessels(data.vessels || []))
      .catch((error) => {
        console.error("Failed to load vessels:", error);
      })
      .finally(() => setLoading(false));
  }, []);

  const classes = [
    "all",
    ...new Set(vessels.map((vessel) => vessel.vessel_class)),
  ];

  const filteredVessels = vessels.filter((vessel) => {
    const matchesSearch =
      vessel.name.toLowerCase().includes(search.toLowerCase()) ||
      vessel.vessel_class.toLowerCase().includes(search.toLowerCase());

    const matchesClass =
      vesselClass === "all" || vessel.vessel_class === vesselClass;

    return matchesSearch && matchesClass;
  });

  return (
    <Page
      title="Vessels"
      subtitle="Explore available vessels and their specifications."
    >
      <Card>
        <div className="fw-directory-head">
          <div className="fw-search inline">
            <Search size={15} />
            <input
              type="text"
              placeholder="Search vessel name, class..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            value={vesselClass}
            onChange={(e) => setVesselClass(e.target.value)}
          >
            {classes.map((item) => (
              <option key={item} value={item}>
                {item === "all" ? "All Vessel Classes" : item}
              </option>
            ))}
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
              {loading ? (
                <tr>
                  <td colSpan="7">Loading vessels...</td>
                </tr>
              ) : filteredVessels.length === 0 ? (
                <tr>
                  <td colSpan="7">No vessels found.</td>
                </tr>
              ) : (
                filteredVessels.map((vessel, index) => (
                  <tr key={vessel.id}>
                    <td>{index + 1}</td>

                    <td>
                      <b>{vessel.name}</b>
                    </td>

                    <td>{vessel.vessel_class}</td>

                    <td>{Number(vessel.dwt).toLocaleString()}</td>

                    <td>{vessel.loa_m}</td>

                    <td>
                      <Badge tone="teal">Available</Badge>
                    </td>

                    <td>
                      <button
                        type="button"
                        className="fw-link"
                        onClick={() => go("new-voyage")}
                      >
                        Use in Voyage
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </Page>
  );
}