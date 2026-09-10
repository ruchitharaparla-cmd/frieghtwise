import React from "react";
import {
  Anchor,
  Clock,
  ArrowUp,
  ArrowDown,
} from "lucide-react";

function PortTable({
  filteredPorts,
  statusFilter,
  setStatusFilter,
}) {
  return (
    <>
      {/* FILTER */}

      <div className="ports-filter-bar">
        <div>
          <h3>East Coast Port Status</h3>

          <p>
            Current operational conditions and waiting times
          </p>
        </div>

        <div className="ports-filter-controls">
          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value)
            }
          >
            <option value="All">
              All Status
            </option>

            <option value="Low">
              Low
            </option>

            <option value="Moderate">
              Moderate
            </option>

            <option value="High">
              High
            </option>
          </select>
        </div>
      </div>

      {/* PORT TABLE */}

      <div className="ports-table-card">
        <div className="ports-table-header">
          <span>Port</span>

          <span>Status</span>

          <span>
            Avg. Waiting Time
          </span>

          <span>
            Congestion
          </span>

          <span>Trend</span>
        </div>

        {filteredPorts.map((port) => (
          <div
            className="ports-table-row"
            key={port.name}
          >
            {/* PORT NAME */}

            <div className="ports-name-cell">
              <div className="ports-anchor-icon">
                <Anchor size={18} />
              </div>

              <div>
                <strong>
                  {port.name}
                </strong>

                <span>
                  {port.location}
                </span>
              </div>
            </div>

            {/* STATUS */}

            <div
              className={`ports-status ${port.statusClass}`}
            >
              <i></i>

              {port.status}
            </div>

            {/* WAITING TIME */}

            <div className="ports-waiting">
              <Clock size={15} />

              {port.waiting}
            </div>

            {/* CONGESTION */}

            <div className="ports-congestion">
              <div className="congestion-bar">
                <span
                  style={{
                    width: port.congestion,
                  }}
                ></span>
              </div>

              <small>
                {port.congestion}
              </small>
            </div>

            {/* TREND */}

            <div
              className={`ports-trend ${port.trend}`}
            >
              {port.trend === "up" ? (
                <ArrowDown size={17} />
              ) : (
                <ArrowUp size={17} />
              )}

              <span>
                {port.trend === "up"
                  ? "Improving"
                  : "Increasing"}
              </span>
            </div>
          </div>
        ))}

        {/* EMPTY STATE */}

        {filteredPorts.length === 0 && (
          <div className="ports-empty">
            <Anchor size={40} />

            <h3>
              No ports found
            </h3>

            <p>
              Try a different search or status filter.
            </p>
          </div>
        )}
      </div>
    </>
  );
}

export default PortTable;