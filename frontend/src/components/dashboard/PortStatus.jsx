import React from "react";
import { useNavigate } from "react-router-dom";

import "./PortStatus.css";


const PortStatus = ({ Icon }) => {

  const navigate = useNavigate();


  const ports = [
    {
      name: "Kolkata",
      status: "Low",
      statusClass: "low",
      waiting: "12 h",
      trend: "▂▃▅▄▆▇",
    },
    {
      name: "Paradip",
      status: "Moderate",
      statusClass: "moderate",
      waiting: "28 h",
      trend: "▂▄▃▅▄▆",
    },
    {
      name: "Visakhapatnam",
      status: "Low",
      statusClass: "low",
      waiting: "16 h",
      trend: "▂▃▄▃▅▆",
    },
    {
      name: "Kakinada",
      status: "Moderate",
      statusClass: "moderate",
      waiting: "24 h",
      trend: "▃▄▃▅▄▆",
    },
    {
      name: "Chennai",
      status: "High",
      statusClass: "high",
      waiting: "46 h",
      trend: "▃▅▄▆▅▇",
    },
    {
      name: "Krishnapatnam",
      status: "Low",
      statusClass: "low",
      waiting: "18 h",
      trend: "▂▃▅▄▆▇",
    },
  ];


  return (

    <div className="panel port-status-panel">


      {/* =================================================
          HEADER
          ================================================= */}

      <div className="panel-header">


        <div>

          <h3>

            <Icon
              type="anchor"
              size={18}
            />

            East Coast Port Status

          </h3>

        </div>


        {/* VIEW ALL PORTS */}

        <button
          type="button"
          className="view-all-button"
          onClick={() => navigate("/ports")}
        >

          View All Ports

          <Icon
            type="arrow"
            size={15}
          />

        </button>


      </div>


      {/* =================================================
          TABLE HEADER
          ================================================= */}

      <div className="port-table">


        <div className="port-table-header">

          <span>
            Port
          </span>

          <span>
            Status
          </span>

          <span>
            Avg. Waiting Time
          </span>

          <span>
            Trend (7 days)
          </span>

        </div>


        {/* =================================================
            PORT ROWS
            ================================================= */}

        {ports.map((port) => (

          <div
            className="port-table-row"
            key={port.name}
          >


            <span className="port-name">

              <Icon
                type="anchor"
                size={14}
              />

              {port.name}

            </span>


            <span
              className={`port-status ${port.statusClass}`}
            >

              <span className="status-dot" />

              {port.status}

            </span>


            <span>
              {port.waiting}
            </span>


            <span className="port-trend">
              {port.trend}
            </span>


          </div>

        ))}


      </div>


    </div>

  );
};


export default PortStatus;