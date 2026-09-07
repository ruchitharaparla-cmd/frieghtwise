import React, { useState } from "react";
import "./Dashboard.css";
import heroShip from "../../assets/images/hero-ship.png";

/* =========================================================
   SIMPLE ICON SYSTEM
   No extra package required.
   This keeps the Dashboard independent of dependencies.
   ========================================================= */

const Icon = ({ type, size = 20, stroke = 2 }) => {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: stroke,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };

  const paths = {
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),

    bell: (
      <>
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
        <path d="M10 21h4" />
      </>
    ),

    chevron: <path d="m7 10 5 5 5-5" />,

    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="m13 6 6 6-6 6" />
      </>
    ),

    home: (
      <>
        <path d="m3 10 9-7 9 7" />
        <path d="M5 9v11h14V9" />
        <path d="M9 20v-6h6v6" />
      </>
    ),

    ship: (
      <>
        <path d="M3 18h18" />
        <path d="M5 18 8 6h8l3 12" />
        <path d="M10 6V3h4v3" />
        <path d="M8 10h8" />
        <path d="M4 21c1.5 0 1.5-1 3-1s1.5 1 3 1 1.5-1 3-1 1.5 1 3 1 1.5-1 3-1" />
      </>
    ),

    chart: (
      <>
        <path d="M4 19V5" />
        <path d="M4 19h17" />
        <path d="m7 15 4-4 3 2 6-7" />
        <path d="M17 6h3v3" />
      </>
    ),

    anchor: (
      <>
        <circle cx="12" cy="5" r="2.5" />
        <path d="M12 7.5v12" />
        <path d="M6 13h12" />
        <path d="M5 17a7 7 0 0 0 14 0" />
      </>
    ),

    location: (
      <>
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </>
    ),

    refresh: (
      <>
        <path d="M20 11a8 8 0 0 0-14-5L3 9" />
        <path d="M3 4v5h5" />
        <path d="M4 13a8 8 0 0 0 14 5l3-3" />
        <path d="M21 20v-5h-5" />
      </>
    ),

    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.7 1.7-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.1h-2.4v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L8 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H6.7v-2.4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L8 8.6l1.7-1.7.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6v-.1h2.4v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.7 1.7-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.1V14h-.1a1.7 1.7 0 0 0-1.6 1Z" />
      </>
    ),

    calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M16 3v4M8 3v4M3 10h18" />
      </>
    ),

    database: (
      <>
        <ellipse cx="12" cy="5" rx="7" ry="3" />
        <path d="M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5" />
        <path d="M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
      </>
    ),

    shield: (
      <>
        <path d="M12 3 20 6v5c0 5-3.4 8.5-8 10-4.6-1.5-8-5-8-10V6l8-3Z" />
        <path d="m8.5 12 2.2 2.2 4.8-5" />
      </>
    ),

    money: (
      <>
        <circle cx="12" cy="12" r="8" />
        <path d="M12 7v10M15 9.5c-.7-.8-1.7-1.2-3-1.2-1.7 0-2.8.8-2.8 2 0 3.2 5.8 1.1 5.8 4 0 1.2-1.1 2-2.9 2-1.3 0-2.4-.4-3.1-1.2" />
      </>
    ),

    box: (
      <>
        <path d="m4 7 8-4 8 4-8 4-8-4Z" />
        <path d="M4 7v10l8 4 8-4V7" />
        <path d="M12 11v10" />
      </>
    ),

    lightbulb: (
      <>
        <path d="M9 18h6" />
        <path d="M10 22h4" />
        <path d="M8.5 15.5C7.5 14.5 7 13.2 7 12a5 5 0 0 1 10 0c0 1.2-.5 2.5-1.5 3.5-.8.8-1.2 1.5-1.3 2.5h-4.4c-.1-1-.5-1.7-1.3-2.5Z" />
      </>
    ),
  };

  return <svg {...common}>{paths[type]}</svg>;
};

/* =========================================================
   DATA
   Temporary UI data.
   Later these values come from the backend.
   ========================================================= */

const initialPorts = [
  {
    name: "Kolkata",
    status: "Low",
    statusClass: "low",
    waiting: "12 h",
    trend: "up",
  },
  {
    name: "Paradip",
    status: "Moderate",
    statusClass: "moderate",
    waiting: "28 h",
    trend: "down",
  },
  {
    name: "Visakhapatnam",
    status: "Low",
    statusClass: "low",
    waiting: "16 h",
    trend: "up",
  },
  {
    name: "Kakinada",
    status: "Moderate",
    statusClass: "moderate",
    waiting: "24 h",
    trend: "down",
  },
  {
    name: "Chennai",
    status: "High",
    statusClass: "high",
    waiting: "46 h",
    trend: "down",
  },
  {
    name: "Krishnapatnam",
    status: "Low",
    statusClass: "low",
    waiting: "18 h",
    trend: "up",
  },
];

const recentVoyages = [
  {
    id: "FW-0268",
    cargo: "Coal",
    route: "Hay Point → Paradip",
    status: "Completed",
    statusClass: "completed",
    cost: "₹6.42 Cr",
  },
  {
    id: "FW-0267",
    cargo: "Iron Ore",
    route: "Port Hedland → Vizag",
    status: "In Transit",
    statusClass: "transit",
    cost: "₹5.98 Cr",
  },
  {
    id: "FW-0266",
    cargo: "Coal",
    route: "Newcastle → Kakinada",
    status: "Loading",
    statusClass: "loading",
    cost: "₹6.21 Cr",
  },
  {
    id: "FW-0265",
    cargo: "Fertilizer",
    route: "Muscat → Chennai",
    status: "Completed",
    statusClass: "completed",
    cost: "₹4.87 Cr",
  },
];

/* =========================================================
   FREIGHT CHART
   ========================================================= */

const FreightChart = () => {
  const historical = [
    [0, 51],
    [7, 45],
    [14, 50],
    [21, 42],
    [28, 47],
    [35, 35],
    [42, 36],
    [49, 32],
    [56, 27],
    [63, 31],
    [70, 28],
    [77, 31],
    [84, 25],
    [91, 34],
  ];

  const forecast = [
    [91, 34],
    [98, 30],
    [105, 27],
    [112, 25],
    [119, 22],
    [126, 20],
    [133, 18],
    [140, 16],
  ];

  const points = (data) =>
    data.map(([x, y]) => `${x * 4.45 + 35},${105 - y * 1.55}`).join(" ");

  return (
    <div className="freight-chart">
      <svg
        viewBox="0 0 690 135"
        preserveAspectRatio="none"
        className="chart-svg"
      >
        {/* horizontal grid */}
        {[20, 40, 60, 80, 100].map((y) => (
          <line
            key={y}
            x1="35"
            x2="660"
            y1={y}
            y2={y}
            className="grid-line"
          />
        ))}

        {/* vertical grid */}
        {[35, 125, 215, 305, 395, 485, 575, 660].map((x) => (
          <line
            key={x}
            x1={x}
            x2={x}
            y1="15"
            y2="105"
            className="grid-line"
          />
        ))}

        {/* forecast confidence area */}
        <path
          d="M440 50 C500 48 550 56 660 64 L660 105 C570 96 500 92 440 70 Z"
          className="confidence-area"
        />

        {/* historical */}
        <polyline
          points={points(historical)}
          className="historical-line"
        />

        {/* forecast */}
        <polyline
          points={points(forecast)}
          className="forecast-line"
        />

        {/* historical points */}
        {historical.map(([x, y], index) => (
          <circle
            key={`h-${index}`}
            cx={x * 4.45 + 35}
            cy={105 - y * 1.55}
            r="2.7"
            className="historical-point"
          />
        ))}

        {/* forecast points */}
        {forecast.map(([x, y], index) => (
          <circle
            key={`f-${index}`}
            cx={x * 4.45 + 35}
            cy={105 - y * 1.55}
            r="2.4"
            className="forecast-point"
          />
        ))}

        {/* today marker */}
        <line
          x1="440"
          x2="440"
          y1="7"
          y2="108"
          className="today-line"
        />

        <rect x="416" y="0" width="48" height="17" rx="4" className="today-label" />
        <text x="440" y="12" textAnchor="middle" className="today-text">
          Today
        </text>

        {/* Y labels */}
        <text x="7" y="24" className="axis-label">50</text>
        <text x="7" y="55" className="axis-label">40</text>
        <text x="7" y="86" className="axis-label">30</text>
        <text x="7" y="106" className="axis-label">20</text>
      </svg>

      <div className="chart-x-labels">
        <span>Aug 11</span>
        <span>Aug 14</span>
        <span>Aug 17</span>
        <span>Aug 20</span>
        <span>Aug 23</span>
        <span>Aug 26</span>
        <span>Aug 29</span>
        <span>Sep 1</span>
        <span>Sep 4</span>
        <span>Sep 7</span>
      </div>

      <div className="chart-legend">
        <span>
          <i className="legend-line historical-legend" />
          Historical
        </span>

        <span>
          <i className="legend-line forecast-legend" />
          Forecast
        </span>

        <span>
          <i className="legend-area" />
          Confidence Range
        </span>
      </div>
    </div>
  );
};

/* =========================================================
   SMALL PORT TREND
   ========================================================= */

const PortTrend = ({ direction }) => {
  const heights =
    direction === "down"
      ? [5, 8, 6, 11, 8, 13, 10]
      : [7, 4, 8, 6, 11, 8, 13];

  return (
    <div className={`port-trend ${direction}`}>
      {heights.map((height, index) => (
        <span
          key={index}
          style={{ height: `${height}px` }}
        />
      ))}
    </div>
  );
};

/* =========================================================
   DASHBOARD
   ========================================================= */

export default function Dashboard() {
  const [range, setRange] = useState("14 Days");
  const [cargo, setCargo] = useState("Coal");

  const handleAnalyze = () => {
    /*
      Later:
      createVoyage(...)
      -> /voyages
      -> /recommend
      -> /forecast

      We intentionally don't put backend logic here yet.
    */

    console.log("Analyze voyage requested");
  };

  return (
    <div className="dashboard-shell">

      {/* ===================================================
          SIDEBAR
          =================================================== */}

      <aside className="dashboard-sidebar">

        <div className="brand">
          <div className="brand-mark">
            <Icon type="ship" size={38} stroke={1.7} />
          </div>

          <div className="brand-name">
            FREIGHTWISE
          </div>

          <div className="brand-tagline">
            Navigate Smarter.<br />
            Charter Better.
          </div>
        </div>

        <nav className="sidebar-navigation">

          <button className="sidebar-item active">
            <Icon type="home" size={21} />
            <span>Dashboard</span>
          </button>

          <button className="sidebar-item">
            <Icon type="arrow" size={21} />
            <span>New Voyage</span>
          </button>

          <button className="sidebar-item">
            <Icon type="chart" size={21} />
            <span>Analysis</span>
          </button>

          <button className="sidebar-item">
            <Icon type="ship" size={21} />
            <span>Vessels</span>
          </button>

          <button className="sidebar-item">
            <Icon type="location" size={21} />
            <span>Ports</span>
          </button>

          <button className="sidebar-item">
            <Icon type="refresh" size={21} />
            <span>Simulation</span>
          </button>

          <button className="sidebar-item">
            <Icon type="settings" size={21} />
            <span>Settings</span>
          </button>

        </nav>

        <div className="sidebar-bottom">

          <div className="engine-status">
            <div className="engine-status-header">
              <span className="online-dot" />
              AI Engine Online
            </div>

            <p>Data updated</p>
            <strong>2 min ago</strong>
          </div>

          <div className="sidebar-wave">
            <span className="wave wave-one" />
            <span className="wave wave-two" />
          </div>

          <div className="sidebar-quote">
            "Smarter Oceans<br />
            for a Stronger India."
          </div>

        </div>

      </aside>

      {/* ===================================================
          MAIN
          =================================================== */}

      <main className="dashboard-main">

        {/* TOP BAR */}

        <header className="topbar">

          <div className="search-box">
            <Icon type="search" size={17} stroke={2} />

            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />
          </div>

          <div className="topbar-right">

            <button className="notification-button">
              <Icon type="bell" size={20} />
              <span>3</span>
            </button>

            <div className="topbar-divider" />

            <div className="avatar">
              K
            </div>

            <div className="user-profile">
              <span>User</span>
              <Icon type="chevron" size={15} />
            </div>

          </div>

        </header>

        <div className="dashboard-content">

          {/* PAGE HEADING */}

          <section className="page-heading">

            <div>
              <h1>Welcome to FreightWise</h1>

              <p>
                AI-Powered Freight &amp; Chartering Intelligence
                for India's East Coast
              </p>
            </div>

            <div className="heading-quote">
              <strong>
                “Efficient Ports.<br />
                Stronger Trade. Brighter Tomorrow.”
              </strong>
            </div>

          </section>

          {/* =================================================
              HERO
              ================================================= */}

          <section
            className="hero-card"
            style={{
              backgroundImage: `url(${heroShip})`,
            }}
          >

            <div className="hero-overlay" />

            <div className="hero-content">

              <h2>
                Smarter Chartering
                <br />
                for a Stronger Tomorrow
              </h2>

              <p>
                Better data. Lower costs. Safer voyages.
              </p>

            </div>

            <div className="hero-features">

              <div>
                <Icon type="chart" size={26} />
                <span>
                  Real-time
                  <small>Market Insights</small>
                </span>
              </div>

              <div>
                <Icon type="ship" size={26} />
                <span>
                  Optimal
                  <small>Vessel Matching</small>
                </span>
              </div>

              <div>
                <Icon type="location" size={26} />
                <span>
                  Smarter
                  <small>Port Selection</small>
                </span>
              </div>

              <div>
                <Icon type="shield" size={26} />
                <span>
                  Lower Risk
                  <small>Higher Savings</small>
                </span>
              </div>

            </div>

            <div className="hero-badge">
              <strong>India's East Coast</strong>
              <span>Connecting Global Opportunities</span>
            </div>

          </section>

          {/* =================================================
              VOYAGE INPUT
              ================================================= */}

          <section className="charter-panel">

            <div className="section-heading">

              <h2>
                What should we charter today?
              </h2>

              <p>
                Enter voyage requirements to get an AI-powered
                chartering recommendation.
              </p>

            </div>

            <div className="charter-form">

              <label>
                <span>Origin Port</span>

                <div className="select-control">
                  <Icon type="anchor" size={16} />
                  <span>Select origin</span>
                  <Icon type="chevron" size={14} />
                </div>
              </label>

              <label>
                <span>Destination Port</span>

                <div className="select-control">
                  <Icon type="anchor" size={16} />
                  <span>Select destination</span>
                  <Icon type="chevron" size={14} />
                </div>
              </label>

              <label>
                <span>Cargo Type</span>

                <select
                  className="native-select"
                  value={cargo}
                  onChange={(e) => setCargo(e.target.value)}
                >
                  <option>Coal</option>
                  <option>Iron Ore</option>
                  <option>Fertilizer</option>
                  <option>Grain</option>
                </select>
              </label>

              <label>
                <span>Quantity (MT)</span>

                <div className="input-control">
                  <Icon type="box" size={16} />

                  <input
                    type="number"
                    defaultValue="75000"
                  />
                </div>
              </label>

              <label>
                <span>Arrival Window</span>

                <div className="select-control">
                  <Icon type="calendar" size={16} />
                  <span>Select dates</span>
                </div>
              </label>

              <button
                className="analyze-button"
                onClick={handleAnalyze}
              >
                Analyze Voyage
                <Icon type="arrow" size={17} />
              </button>

            </div>

          </section>

          {/* =================================================
              KPI CARDS
              ================================================= */}

          <section className="metrics-grid">

            <div className="metric-card">

              <div className="metric-icon blue">
                <Icon type="database" size={27} />
              </div>

              <div className="metric-content">
                <span className="metric-title">
                  Current Freight Rate
                </span>

                <strong>
                  $24.8 / MT
                </strong>

                <span className="metric-subtitle positive">
                  ↓ 6.2% expected
                </span>
              </div>

              <div className="metric-decoration">
                <Icon type="chart" size={52} />
              </div>

            </div>

            <div className="metric-card">

              <div className="metric-icon green">
                <Icon type="calendar" size={27} />
              </div>

              <div className="metric-content">
                <span className="metric-title">
                  Best Chartering Window
                </span>

                <strong>
                  12 – 18 Sep
                </strong>

                <span className="metric-subtitle positive">
                  AI suggested
                </span>
              </div>

              <div className="metric-decoration">
                <Icon type="calendar" size={48} />
              </div>

            </div>

            <div className="metric-card">

              <div className="metric-icon emerald">
                <Icon type="shield" size={28} />
              </div>

              <div className="metric-content">
                <span className="metric-title">
                  Risk Score
                </span>

                <strong>
                  32 / 100
                </strong>

                <span className="metric-subtitle positive">
                  Low Risk
                </span>
              </div>

              <div className="metric-decoration">
                <Icon type="chart" size={50} />
              </div>

            </div>

            <div className="metric-card">

              <div className="metric-icon sky">
                <Icon type="money" size={27} />
              </div>

              <div className="metric-content">
                <span className="metric-title">
                  Expected Savings
                </span>

                <strong>
                  ₹18.4 L
                </strong>

                <span className="metric-subtitle">
                  vs. current market
                </span>
              </div>

              <div className="metric-decoration">
                <Icon type="chart" size={52} />
              </div>

            </div>

          </section>

          {/* =================================================
              ANALYTICS
              ================================================= */}

          <section className="analytics-grid">

            {/* FREIGHT CHART */}

            <div className="panel freight-panel">

              <div className="panel-header">

                <div>
                  <h3>
                    <Icon type="chart" size={18} />
                    Freight Rate Trend
                  </h3>

                  <span>
                    Freight Rate (USD/MT)
                  </span>
                </div>

                <div className="range-buttons">

                  {["7 Days", "14 Days", "30 Days"].map((item) => (
                    <button
                      key={item}
                      className={range === item ? "selected" : ""}
                      onClick={() => setRange(item)}
                    >
                      {item}
                    </button>
                  ))}

                </div>

              </div>

              <div className="chart-container">
                <FreightChart />
              </div>

            </div>

            {/* PORT STATUS */}

            <div className="panel port-panel">

              <div className="panel-header">

                <h3>
                  <Icon type="anchor" size={18} />
                  East Coast Port Status
                </h3>

                <button className="view-link">
                  View All Ports
                  <Icon type="arrow" size={12} />
                </button>

              </div>

              <div className="port-table">

                <div className="port-row table-heading">
                  <span>Port</span>
                  <span>Status</span>
                  <span>Avg. Waiting Time</span>
                  <span>Trend (7 days)</span>
                </div>

                {initialPorts.map((port) => (
                  <div className="port-row" key={port.name}>

                    <div className="port-name">
                      <Icon type="anchor" size={13} />
                      {port.name}
                    </div>

                    <div
                      className={`port-status ${port.statusClass}`}
                    >
                      <i />
                      {port.status}
                    </div>

                    <span>
                      {port.waiting}
                    </span>

                    <PortTrend direction={port.trend} />

                  </div>
                ))}

              </div>

            </div>

            {/* RECENT VOYAGES */}

            <div className="panel voyages-panel">

              <div className="panel-header">

                <h3>
                  <Icon type="ship" size={18} />
                  Recent Voyages
                </h3>

                <button className="view-link">
                  View All
                  <Icon type="arrow" size={12} />
                </button>

              </div>

              <div className="voyage-table">

                <div className="voyage-row table-heading">
                  <span>Voyage</span>
                  <span>Cargo</span>
                  <span>Route</span>
                  <span>Status</span>
                  <span>Cost</span>
                </div>

                {recentVoyages.map((voyage) => (
                  <div
                    className="voyage-row"
                    key={voyage.id}
                  >

                    <div className="voyage-id">

                      <div className="ship-thumbnail">
                        <Icon type="ship" size={17} />
                      </div>

                      {voyage.id}

                    </div>

                    <span>{voyage.cargo}</span>

                    <span>{voyage.route}</span>

                    <span
                      className={`voyage-status ${voyage.statusClass}`}
                    >
                      <i />
                      {voyage.status}
                    </span>

                    <strong>
                      {voyage.cost}
                    </strong>

                  </div>
                ))}

              </div>

            </div>

            {/* AI INSIGHT */}

            <div className="panel insight-panel">

              <div className="insight-icon">
                <Icon type="lightbulb" size={29} />
              </div>

              <div className="insight-content">

                <div className="insight-header">

                  <h3>
                    AI Market Insight
                  </h3>

                  <span>
                    Today, 10:24 AM
                  </span>

                </div>

                <p>
                  Freight rates are expected to decline over the
                  next 10 days. FreightWise suggests monitoring
                  the current market before locking a vessel.
                </p>

                <ul>
                  <li>
                    Declining trend in global coal freight rates
                  </li>

                  <li>
                    Lower congestion expected at Paradip
                  </li>

                  <li>
                    Favourable weather conditions in Bay of Bengal
                  </li>
                </ul>

              </div>

              <div className="insight-graph">
                <Icon type="chart" size={88} />
              </div>

            </div>

          </section>

        </div>

      </main>

    </div>
  );
}