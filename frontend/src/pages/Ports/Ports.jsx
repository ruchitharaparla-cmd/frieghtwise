import React from "react";
import "./Ports.css";

import portImage from "../../assets/images/port.png";
import mapImage from "../../assets/images/mapplaceholder.png";

const ports = [
  {
    name: "Kolkata",
    status: "Operational",
    statusType: "low",
    draft: "13.5",
    waiting: "12 h",
    congestion: "Low",
    weather: "Low",
    cargo: "Coal, Fertilizer, Containers",
  },
  {
    name: "Paradip",
    status: "Operational",
    statusType: "moderate",
    draft: "14.5",
    waiting: "28 h",
    congestion: "Moderate",
    weather: "Low",
    cargo: "Coal, Iron Ore, Fertilizer",
  },
  {
    name: "Visakhapatnam",
    status: "Operational",
    statusType: "low",
    draft: "16.0",
    waiting: "16 h",
    congestion: "Low",
    weather: "Moderate",
    cargo: "Coal, Alumina, Containers",
  },
  {
    name: "Kakinada",
    status: "Operational",
    statusType: "moderate",
    draft: "14.0",
    waiting: "24 h",
    congestion: "Moderate",
    weather: "Low",
    cargo: "Fertilizer, Agriculture, Coal",
  },
  {
    name: "Chennai",
    status: "Congested",
    statusType: "high",
    draft: "13.0",
    waiting: "46 h",
    congestion: "High",
    weather: "Moderate",
    cargo: "Containers, Coal, Automotive",
  },
  {
    name: "Krishnapatnam",
    status: "Operational",
    statusType: "low",
    draft: "14.0",
    waiting: "18 h",
    congestion: "Low",
    weather: "Low",
    cargo: "Coal, Cement, Containers",
  },
];

const congestionData = [
  { name: "Kolkata", value: 12, type: "low" },
  { name: "Paradip", value: 28, type: "moderate" },
  { name: "Vizag", value: 16, type: "low" },
  { name: "Kakinada", value: 24, type: "moderate" },
  { name: "Chennai", value: 46, type: "high" },
  { name: "Krishnapatnam", value: 18, type: "low" },
];

function Ports() {
  return (
    <div className="ports-page">

      {/* ================= SIDEBAR ================= */}
      <aside className="ports-sidebar">

        <div className="brand">
          <div className="brand-icon">⚓</div>

          <div className="brand-name">
            FREIGHTWISE
          </div>

          <div className="brand-tagline">
            Navigate Smarter.
            <br />
            Charter Better.
          </div>
        </div>

        <nav className="sidebar-nav">

          <a href="#" className="nav-item">
            <span className="nav-icon">⌂</span>
            <span>Dashboard</span>
          </a>

          <a href="#" className="nav-item">
            <span className="nav-icon">➤</span>
            <span>New Voyage</span>
          </a>

          <a href="#" className="nav-item">
            <span className="nav-icon">▥</span>
            <span>Analysis</span>
          </a>

          <a href="#" className="nav-item">
            <span className="nav-icon">⚓</span>
            <span>Vessels</span>
          </a>

          <a href="#" className="nav-item active">
            <span className="nav-icon">⌖</span>
            <span>Ports</span>
          </a>

          <a href="#" className="nav-item">
            <span className="nav-icon">⟳</span>
            <span>Simulation</span>
          </a>

          <a href="#" className="nav-item">
            <span className="nav-icon">⚙</span>
            <span>Settings</span>
          </a>

        </nav>

        <div className="engine-card">
          <div className="engine-status">
            <span className="online-dot"></span>
            <strong>AI Engine Online</strong>
          </div>

          <div className="engine-text">
            Data updated
            <br />
            2 min ago
          </div>
        </div>

        <div className="sidebar-wave">
          <div className="wave-line wave-one"></div>
          <div className="wave-line wave-two"></div>
          <div className="wave-line wave-three"></div>
        </div>

        <div className="sidebar-quote">
          “Stronger Ports.
          <br />
          A Stronger India.”
        </div>

      </aside>


      {/* ================= MAIN AREA ================= */}
      <main className="ports-main">

        {/* TOP BAR */}
        <header className="topbar">

          <div className="search-box">
            <span className="search-icon">⌕</span>
            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />
          </div>

          <div className="topbar-right">

            <span className="notification">
              ♧
              <b>3</b>
            </span>

            <span className="divider"></span>

            <div className="user-avatar">
              K
            </div>

            <span className="user-name">
              User
            </span>

            <span className="dropdown-arrow">
              ˅
            </span>

          </div>

        </header>


        {/* PAGE HEADER */}
        <section className="page-header">

          <div>
            <h1>Port &amp; Route Intelligence</h1>

            <p>
              Explore ports, route conditions and operational risks
            </p>
          </div>

          <div className="header-message">
            <strong>
              “Connected Ports.
              <br />
              Stronger Routes. Greater Opportunities.”
            </strong>
          </div>

          <div className="header-date">
            Mon, 25 Aug 2026&nbsp;&nbsp; | &nbsp;&nbsp;14:32 IST
          </div>

        </section>


        {/* ================= TOP CONTENT ================= */}
        <section className="top-content">

          {/* ---------- MAP ---------- */}
          <div className="map-card">

            {/* IMPORTANT:
                ONLY map image.
                No extra port markers here.
                This prevents duplicate markers.
            */}
            <img
              src={mapImage}
              alt="East Coast India port route map"
              className="map-image"
            />

          </div>


          {/* ---------- RIGHT COLUMN ---------- */}
          <div className="right-column">

            {/* PARADIP PORT CARD */}
            <section className="port-detail-card">

              <div className="detail-title-row">

                <h2>Paradip Port</h2>

                <span className="operational-badge">
                  Operational
                </span>

              </div>


              <img
                src={portImage}
                alt="Paradip Port"
                className="port-image"
              />


              <div className="location-row">

                <span className="location-icon">
                  ⌖
                </span>

                <span>
                  Paradip, Odisha, India
                </span>

                <a href="#">
                  View on Map ↗
                </a>

              </div>


              <div className="port-stats">

                <div className="stat-box">

                  <span className="stat-icon">
                    ⚓
                  </span>

                  <div>
                    <span className="stat-label">
                      Max Draft
                    </span>

                    <strong>
                      14.5 m
                    </strong>
                  </div>

                </div>


                <div className="stat-box">

                  <span className="stat-icon">
                    ◷
                  </span>

                  <div>
                    <span className="stat-label">
                      Avg. Waiting Time
                    </span>

                    <strong>
                      28 h
                    </strong>
                  </div>

                </div>


                <div className="stat-box">

                  <span className="stat-icon orange-icon">
                    ▥
                  </span>

                  <div>
                    <span className="stat-label">
                      Congestion
                    </span>

                    <strong className="orange-text">
                      Moderate
                    </strong>
                  </div>

                </div>


                <div className="stat-box">

                  <span className="stat-icon">
                    ▣
                  </span>

                  <div>
                    <span className="stat-label">
                      Cargo Handled
                    </span>

                    <strong className="small-stat">
                      Coal, Iron Ore, Fertilizer
                    </strong>
                  </div>

                </div>


                <div className="stat-box">

                  <span className="stat-icon green-icon">
                    ☁
                  </span>

                  <div>
                    <span className="stat-label">
                      Weather Risk
                    </span>

                    <strong className="green-text">
                      Low
                    </strong>
                  </div>

                </div>


                <div className="stat-box">

                  <span className="stat-icon">
                    ▤
                  </span>

                  <div>
                    <span className="stat-label">
                      Port Charges
                    </span>

                    <strong>
                      $12.5 / MT
                    </strong>
                  </div>

                </div>

              </div>

            </section>


            {/* ---------- CONGESTION TREND ---------- */}
            <section className="congestion-card">

              <div className="congestion-header">

                <div className="congestion-title">

                  <span className="trend-icon">
                    ◆
                  </span>

                  <h3>
                    Port Congestion Trend
                  </h3>

                </div>

                <select defaultValue="30">
                  <option value="30">
                    Last 30 Days
                  </option>

                  <option value="7">
                    Last 7 Days
                  </option>

                  <option value="90">
                    Last 90 Days
                  </option>
                </select>

              </div>


              <div className="chart-area">

                <div className="y-axis">

                  <span>60</span>
                  <span>40</span>
                  <span>20</span>
                  <span>0</span>

                </div>


                <div className="chart-content">

                  <div className="grid-line line-60"></div>
                  <div className="grid-line line-40"></div>
                  <div className="grid-line line-20"></div>
                  <div className="grid-line line-0"></div>


                  <div className="bars">

                    {congestionData.map((item) => (
                      <div
                        className="bar-column"
                        key={item.name}
                      >

                        <span className="bar-value">
                          {item.value}h
                        </span>

                        <div
                          className={`bar ${item.type}`}
                          style={{
                            height: `${item.value * 1.45}px`,
                          }}
                        ></div>

                        <span className="bar-label">
                          {item.name}
                        </span>

                      </div>
                    ))}

                  </div>

                </div>

              </div>

            </section>

          </div>

        </section>


        {/* ================= BOTTOM TABLE ================= */}
        <section className="overview-card">

          <div className="overview-header">

            <div className="overview-title">

              <span className="overview-icon">
                ⚓
              </span>

              <div>
                <h2>
                  East Coast Ports Overview
                </h2>

                <p>
                  Real-time port conditions, capacity and operational information
                </p>
              </div>

            </div>

          </div>


          <div className="table-wrapper">

            <table>

              <thead>
                <tr>
                  <th>Port</th>
                  <th>Status</th>
                  <th>Max Draft (m)</th>
                  <th>Avg. Waiting Time</th>
                  <th>Congestion</th>
                  <th>Weather Risk</th>
                  <th>Cargo Capability</th>
                  <th>Actions</th>
                </tr>
              </thead>


              <tbody>

                {ports.map((port) => (
                  <tr key={port.name}>

                    <td className="port-name">
                      {port.name}
                    </td>


                    <td>
                      <span
                        className={`status-pill ${port.statusType}`}
                      >
                        <span className="status-dot"></span>
                        {port.status}
                      </span>
                    </td>


                    <td>
                      {port.draft}
                    </td>


                    <td>
                      {port.waiting}
                    </td>


                    <td>
                      <span
                        className={`risk-pill ${port.statusType}`}
                      >
                        <span className="status-dot"></span>
                        {port.congestion}
                      </span>
                    </td>


                    <td>
                      <span
                        className={`risk-pill ${
                          port.weather === "Low"
                            ? "low"
                            : "moderate"
                        }`}
                      >
                        <span className="status-dot"></span>
                        {port.weather}
                      </span>
                    </td>


                    <td className="cargo-cell">
                      {port.cargo}
                    </td>


                    <td>
                      <button className="view-button">
                        View Details
                      </button>
                    </td>

                  </tr>
                ))}

              </tbody>

            </table>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Ports;