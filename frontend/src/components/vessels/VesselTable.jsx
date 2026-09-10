import React from "react";
import { Ship } from "lucide-react";

import {
  FitBadge,
  AvailabilityBadge,
} from "./CompatibilityBadge";

import "./VesselTable.css";

export default function VesselTable({
  vessels,
  onViewDetails,
}) {
  return (
    <section className="all-vessels-card">

      <div className="all-vessels-header">

        <div className="all-vessels-heading">

          <Ship
            size={29}
            strokeWidth={2}
          />

          <div>
            <h2>All Available Vessels</h2>

            <p>
              Compare vessels based on compatibility,
              availability and estimated cost
            </p>
          </div>

        </div>

        <div className="table-toolbar">

          <span>
            Showing{" "}
            <strong>
              {vessels.length}
            </strong>{" "}
            vessels
          </span>

          <label>
            Sort by

            <select defaultValue="recommended">
              <option value="recommended">
                Recommended
              </option>

              <option value="cost">
                Lowest Cost
              </option>

              <option value="dwt">
                DWT
              </option>
            </select>

          </label>

        </div>

      </div>

      <div className="table-container">

        <table className="vessel-table">

          <thead>
            <tr>
              <th>Vessel</th>
              <th>DWT</th>
              <th>Type</th>
              <th>Cargo Fit</th>
              <th>Port Fit</th>
              <th>Availability</th>
              <th>Estimated Cost</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>

            {vessels.map((vessel) => (
              <tr key={vessel.id}>

                <td>
                  <div className="table-vessel">

                    <img
                      src={vessel.image}
                      alt=""
                    />

                    <strong>
                      {vessel.name}
                    </strong>

                  </div>
                </td>

                <td>
                  {vessel.dwt.toLocaleString()}
                </td>

                <td>
                  {vessel.type}
                </td>

                <td>
                  <FitBadge
                    value={vessel.cargoFit}
                  />
                </td>

                <td>
                  <FitBadge
                    value={vessel.portFit}
                  />
                </td>

                <td>
                  <AvailabilityBadge
                    value={vessel.availability}
                  />
                </td>

                <td>
                  <div className="table-cost">

                    <strong>
                      {typeof vessel.cost === "number" ? `₹ ${vessel.cost.toFixed(2)} Cr` : "Unavailable"}
                    </strong>

                    <span>
                      {typeof vessel.costPerMt === "number" ? `($${vessel.costPerMt.toFixed(1)} / MT)` : "(N/A)"}
                    </span>

                  </div>
                </td>

                <td>
                  <button
                    className="table-details-button"
                    onClick={() =>
                      onViewDetails(vessel)
                    }
                  >
                    View Details
                  </button>
                </td>

              </tr>
            ))}

          </tbody>

        </table>

      </div>

    </section>
  );
}