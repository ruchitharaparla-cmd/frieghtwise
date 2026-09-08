import React, { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Search,
  Bell,
  ChevronDown,
  LayoutDashboard,
  ArrowRight,
  ArrowLeft,
  BarChart3,
  Ship,
  Anchor,
  RotateCcw,
  Settings,
  MapPin,
  CalendarDays,
  Database,
  ShieldCheck,
  CircleDollarSign,
  Package,
  Lightbulb,
} from "lucide-react";

import "./Dashboard.css";
import heroImage from "../../assets/images/hero-ship.png";


/* =========================================================
   PORTS
========================================================= */

const ports = [
  "Kolkata",
  "Paradip",
  "Visakhapatnam",
  "Kakinada",
  "Chennai",
  "Krishnapatnam",
];


/* =========================================================
   PORT STATUS
========================================================= */

const portData = [
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


/* =========================================================
   RECENT VOYAGES
========================================================= */

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
   FREIGHT DATA
========================================================= */

const freightData = {
  "7 Days": {
    labels: [
      "Sep 1",
      "Sep 2",
      "Sep 3",
      "Sep 4",
      "Sep 5",
      "Sep 6",
      "Sep 7",
    ],
    historical: [36, 38, 35, 34, 32, 31, 30],
    forecast: [30, 29, 28, 27, 26, 25, 24],
  },

  "14 Days": {
    labels: [
      "Aug 25",
      "Aug 27",
      "Aug 29",
      "Aug 31",
      "Sep 2",
      "Sep 4",
      "Sep 6",
      "Sep 7",
    ],
    historical: [40, 36, 39, 35, 38, 34, 37, 33],
    forecast: [33, 31, 29, 28, 27, 26, 25, 24],
  },

  "30 Days": {
    labels: [
      "Aug 9",
      "Aug 13",
      "Aug 17",
      "Aug 21",
      "Aug 25",
      "Aug 29",
      "Sep 2",
      "Sep 7",
    ],
    historical: [49, 45, 44, 40, 36, 38, 34, 33],
    forecast: [33, 31, 29, 27, 25, 24, 23, 22],
  },
};


/* =========================================================
   FREIGHT CHART
========================================================= */

function FreightChart({ selectedRange, navigationIndex }) {

  const dataset = freightData[selectedRange];

  const maxValue = 55;
  const minValue = 15;

  const width = 690;
  const height = 145;

  const left = 40;
  const right = 15;
  const top = 15;
  const bottom = 30;

  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;


  const points = dataset.historical.map((value, index) => {

    const x =
      left +
      (index /
        Math.max(dataset.historical.length - 1, 1)) *
        chartWidth;

    const y =
      top +
      ((maxValue - value) /
        (maxValue - minValue)) *
        chartHeight;

    return {
      x,
      y,
      value,
    };
  });


  const forecastPoints = dataset.forecast.map(
    (value, index) => {

      const x =
        left +
        (index /
          Math.max(dataset.forecast.length - 1, 1)) *
          chartWidth;

      const y =
        top +
        ((maxValue - value) /
          (maxValue - minValue)) *
          chartHeight;

      return {
        x,
        y,
        value,
      };
    }
  );


  const historicalPath = points
    .map((point, index) =>
      `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`
    )
    .join(" ");


  const forecastPath = forecastPoints
    .map((point, index) =>
      `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`
    )
    .join(" ");


  const todayIndex =
    Math.max(
      0,
      points.length - 1
    );


  const todayPoint = points[todayIndex];


  return (
    <div className="freight-chart">

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="chart-svg"
        preserveAspectRatio="none"
      >

        {/* GRID */}

        {[20, 30, 40, 50].map((value) => {

          const y =
            top +
            ((maxValue - value) /
              (maxValue - minValue)) *
              chartHeight;

          return (
            <g key={value}>

              <line
                x1={left}
                x2={width - right}
                y1={y}
                y2={y}
                className="grid-line"
              />

              <text
                x="7"
                y={y + 3}
                className="axis-label"
              >
                {value}
              </text>

            </g>
          );
        })}


        {/* VERTICAL GRID */}

        {dataset.labels.map((_, index) => {

          const x =
            left +
            (index /
              Math.max(dataset.labels.length - 1, 1)) *
              chartWidth;

          return (
            <line
              key={index}
              x1={x}
              x2={x}
              y1={top}
              y2={height - bottom}
              className="grid-line vertical"
            />
          );
        })}


        {/* CONFIDENCE AREA */}

        <path
          d={`
            M ${forecastPoints[0].x} ${forecastPoints[0].y - 8}
            ${forecastPoints
              .map(
                (point) =>
                  `L ${point.x} ${point.y - 8}`
              )
              .join(" ")}
            ${forecastPoints
              .slice()
              .reverse()
              .map(
                (point) =>
                  `L ${point.x} ${point.y + 12}`
              )
              .join(" ")}
            Z
          `}
          className="confidence-area"
        />


        {/* HISTORICAL */}

        <path
          d={historicalPath}
          className="historical-line"
        />


        {/* FORECAST */}

        <path
          d={forecastPath}
          className="forecast-line"
        />


        {/* HISTORICAL POINTS */}

        {points.map((point, index) => (

          <circle
            key={`history-${index}`}
            cx={point.x}
            cy={point.y}
            r="3"
            className="historical-point"
          />

        ))}


        {/* FORECAST POINTS */}

        {forecastPoints.map((point, index) => (

          <circle
            key={`forecast-${index}`}
            cx={point.x}
            cy={point.y}
            r="2.6"
            className="forecast-point"
          />

        ))}


        {/* TODAY LINE */}

        <line
          x1={todayPoint.x}
          x2={todayPoint.x}
          y1="7"
          y2={height - bottom + 2}
          className="today-line"
        />


        <rect
          x={todayPoint.x - 24}
          y="0"
          width="48"
          height="17"
          rx="4"
          className="today-label"
        />


        <text
          x={todayPoint.x}
          y="12"
          textAnchor="middle"
          className="today-text"
        >
          Today
        </text>


        {/* X AXIS */}

        {dataset.labels.map((label, index) => {

          const x =
            left +
            (index /
              Math.max(dataset.labels.length - 1, 1)) *
              chartWidth;

          return (
            <text
              key={label}
              x={x}
              y={height - 7}
              textAnchor="middle"
              className="axis-label"
            >
              {label}
            </text>
          );
        })}

      </svg>


      <div className="chart-navigation">

        <button
          type="button"
          className="chart-nav-button"
          disabled={navigationIndex === 0}
          title="Previous period"
        >
          <ArrowLeft size={12} />
        </button>


        <div className="chart-position">
          Period {navigationIndex + 1}
        </div>


        <button
          type="button"
          className="chart-nav-button"
          disabled
          title="Next period"
        >
          <ArrowRight size={12} />
        </button>

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
}


/* =========================================================
   PORT TREND
========================================================= */

function PortTrend({ direction }) {

  const heights =
    direction === "down"
      ? [5, 8, 6, 11, 8, 13, 10]
      : [7, 4, 8, 6, 11, 8, 13];


  return (
    <div className={`port-trend ${direction}`}>

      {heights.map((height, index) => (

        <span
          key={index}
          style={{
            height: `${height}px`,
          }}
        />

      ))}

    </div>
  );
}


/* =========================================================
   DASHBOARD
========================================================= */

export default function Dashboard() {

  const navigate = useNavigate();


  /* FORM */

  const [originPort, setOriginPort] =
    useState("");

  const [destinationPort, setDestinationPort] =
    useState("");

  const [cargoType, setCargoType] =
    useState("Coal");

  const [quantity, setQuantity] =
    useState("75000");

  const [arrivalFrom, setArrivalFrom] =
    useState("");

  const [arrivalTo, setArrivalTo] =
    useState("");


  /* CHART */

  const [range, setRange] =
    useState("14 Days");

  const [navigationIndex, setNavigationIndex] =
    useState(0);


  /* =======================================================
     ORIGIN
  ======================================================= */

  const handleOriginChange = (event) => {

    const value = event.target.value;

    setOriginPort(value);

    if (value === destinationPort) {
      setDestinationPort("");
    }
  };


  /* =======================================================
     DESTINATION
  ======================================================= */

  const handleDestinationChange = (event) => {

    const value = event.target.value;

    if (value === originPort) {
      return;
    }

    setDestinationPort(value);
  };


  /* =======================================================
     ARRIVAL FROM
  ======================================================= */

  const handleArrivalFromChange = (event) => {

    const value = event.target.value;

    setArrivalFrom(value);

    if (arrivalTo && value > arrivalTo) {
      setArrivalTo("");
    }
  };


  /* =======================================================
     ARRIVAL TO
  ======================================================= */

  const handleArrivalToChange = (event) => {

    const value = event.target.value;

    if (
      arrivalFrom &&
      value < arrivalFrom
    ) {
      return;
    }

    setArrivalTo(value);
  };


  /* =======================================================
     ANALYZE
  ======================================================= */

  const handleAnalyzeVoyage = () => {

    if (!originPort) {
      alert("Please select an origin port.");
      return;
    }

    if (!destinationPort) {
      alert("Please select a destination port.");
      return;
    }

    if (originPort === destinationPort) {
      alert(
        "Origin and destination ports must be different."
      );
      return;
    }

    if (!arrivalFrom || !arrivalTo) {
      alert(
        "Please select the complete arrival window."
      );
      return;
    }


    const params = new URLSearchParams({

      origin: originPort,

      destination: destinationPort,

      cargo: cargoType,

      quantity,

      arrivalFrom,

      arrivalTo,

    });


    navigate(
      `/new-voyage?${params.toString()}`
    );
  };


  /* =======================================================
     RANGE CHANGE
  ======================================================= */

  const handleRangeChange = (newRange) => {

    setRange(newRange);

    /*
      Reset chart navigation whenever
      the time range changes.
    */

    setNavigationIndex(0);
  };


  return (
    <div className="dashboard-shell">


      {/* =================================================
          SIDEBAR
      ================================================= */}

      <aside className="dashboard-sidebar">

        <div className="brand">

          <div className="brand-mark">
            <Ship
              size={38}
              strokeWidth={1.7}
            />
          </div>

          <div className="brand-name">
            FREIGHTWISE
          </div>

          <div className="brand-tagline">
            Navigate Smarter.
            <br />
            Charter Better.
          </div>

        </div>


        <nav className="sidebar-navigation">

          <Link
            to="/"
            className="sidebar-item active"
          >
            <LayoutDashboard size={21} />
            <span>Dashboard</span>
          </Link>


          <Link
            to="/new-voyage"
            className="sidebar-item"
          >
            <ArrowRight size={21} />
            <span>New Voyage</span>
          </Link>


          <Link
            to="/analysis"
            className="sidebar-item"
          >
            <BarChart3 size={21} />
            <span>Analysis</span>
          </Link>


          <Link
            to="/vessels"
            className="sidebar-item"
          >
            <Ship size={21} />
            <span>Vessels</span>
          </Link>


          <Link
            to="/ports"
            className="sidebar-item"
          >
            <MapPin size={21} />
            <span>Ports</span>
          </Link>


          <Link
            to="/simulation"
            className="sidebar-item"
          >
            <RotateCcw size={21} />
            <span>Simulation</span>
          </Link>


          <Link
            to="/settings"
            className="sidebar-item"
          >
            <Settings size={21} />
            <span>Settings</span>
          </Link>

        </nav>


        <div className="sidebar-bottom">

          <div className="engine-status">

            <div className="engine-status-header">

              <span className="online-dot" />

              AI Engine Online

            </div>

            <p>
              Data updated
            </p>

            <strong>
              2 min ago
            </strong>

          </div>


          <div className="sidebar-wave">

            <span className="wave wave-one" />

            <span className="wave wave-two" />

          </div>


          <div className="sidebar-quote">

            "Smarter Oceans
            <br />
            for a Stronger India."

          </div>

        </div>

      </aside>


      {/* =================================================
          MAIN
      ================================================= */}

      <main className="dashboard-main">


        {/* TOP BAR */}

        <header className="topbar">

          <div className="search-box">

            <Search size={17} />

            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />

          </div>


          <div className="topbar-right">

            <Link
              to="/notifications"
              className="notification-button"
            >

              <Bell size={20} />

              <span>3</span>

            </Link>


            <div className="topbar-divider" />


            <Link
              to="/profile"
              className="user-profile-link"
            >

              <div className="avatar">
                K
              </div>

              <div className="user-profile">

                <span>
                  User
                </span>

                <ChevronDown size={15} />

              </div>

            </Link>

          </div>

        </header>


        <div className="dashboard-content">


          {/* PAGE HEADING */}

          <section className="page-heading">

            <div>

              <h1>
                Welcome to FreightWise
              </h1>

              <p>
                AI-Powered Freight &amp; Chartering
                Intelligence for India's East Coast
              </p>

            </div>


            <div className="heading-quote">

              <strong>
                “Efficient Ports.
                <br />
                Stronger Trade. Brighter Tomorrow.”
              </strong>

            </div>

          </section>


          {/* HERO */}

          <section
            className="hero-card"
            style={{
              backgroundImage:
                `url(${heroImage})`,
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
                <BarChart3 size={26} />

                <span>
                  Real-time
                  <small>
                    Market Insights
                  </small>
                </span>
              </div>


              <div>
                <Ship size={26} />

                <span>
                  Optimal
                  <small>
                    Vessel Matching
                  </small>
                </span>
              </div>


              <div>
                <MapPin size={26} />

                <span>
                  Smarter
                  <small>
                    Port Selection
                  </small>
                </span>
              </div>


              <div>
                <ShieldCheck size={26} />

                <span>
                  Lower Risk
                  <small>
                    Higher Savings
                  </small>
                </span>
              </div>

            </div>


            <div className="hero-badge">

              <strong>
                India's East Coast
              </strong>

              <span>
                Connecting Global Opportunities
              </span>

            </div>

          </section>


          {/* =================================================
              CHARTER FORM
          ================================================= */}

          <section className="charter-panel">

            <div className="section-heading">

              <h2>
                What should we charter today?
              </h2>

              <p>
                Enter voyage requirements to get an
                AI-powered chartering recommendation.
              </p>

            </div>


            <div className="charter-form">


              {/* ORIGIN */}

              <label className="form-field">

                <span>
                  Origin Port
                </span>


                <div className="select-wrapper">

                  <Anchor
                    size={16}
                    className="field-icon"
                  />


                  <select
                    value={originPort}
                    onChange={handleOriginChange}
                    className="port-select"
                  >

                    <option value="">
                      Select origin
                    </option>


                    {ports.map((port) => (

                      <option
                        key={port}
                        value={port}
                      >
                        {port}
                      </option>

                    ))}

                  </select>


                  <ChevronDown
                    size={14}
                    className="select-arrow"
                  />

                </div>

              </label>


              {/* DESTINATION */}

              <label className="form-field">

                <span>
                  Destination Port
                </span>


                <div className="select-wrapper">

                  <Anchor
                    size={16}
                    className="field-icon"
                  />


                  <select
                    value={destinationPort}
                    onChange={handleDestinationChange}
                    className="port-select"
                  >

                    <option value="">
                      Select destination
                    </option>


                    {ports.map((port) => (

                      <option
                        key={port}
                        value={port}
                        disabled={
                          port === originPort
                        }
                      >
                        {port}
                        {port === originPort
                          ? " (Origin)"
                          : ""}
                      </option>

                    ))}

                  </select>


                  <ChevronDown
                    size={14}
                    className="select-arrow"
                  />

                </div>

              </label>


              {/* CARGO */}

              <label className="form-field">

                <span>
                  Cargo Type
                </span>


                <div className="select-wrapper">

                  <select
                    value={cargoType}
                    onChange={(event) =>
                      setCargoType(
                        event.target.value
                      )
                    }
                    className="cargo-select"
                  >

                    <option value="Coal">
                      Coal
                    </option>

                    <option value="Iron Ore">
                      Iron Ore
                    </option>

                    <option value="Fertilizer">
                      Fertilizer
                    </option>

                    <option value="Grain">
                      Grain
                    </option>

                  </select>


                  <ChevronDown
                    size={14}
                    className="select-arrow"
                  />

                </div>

              </label>


              {/* QUANTITY */}

              <label className="form-field">

                <span>
                  Quantity (MT)
                </span>


                <div className="input-control">

                  <Package size={16} />

                  <input
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(event) =>
                      setQuantity(
                        event.target.value
                      )
                    }
                  />

                </div>

              </label>


              {/* ARRIVAL */}

              <div className="arrival-window-field">

                <span>
                  Arrival Window
                </span>


                <div className="date-range-control">

                  <CalendarDays
                    size={16}
                    className="calendar-icon"
                  />


                  <input
                    type="date"
                    value={arrivalFrom}
                    onChange={
                      handleArrivalFromChange
                    }
                  />


                  <span className="date-separator">
                    →
                  </span>


                  <input
                    type="date"
                    value={arrivalTo}
                    min={
                      arrivalFrom || undefined
                    }
                    disabled={!arrivalFrom}
                    onChange={
                      handleArrivalToChange
                    }
                  />

                </div>

              </div>


              {/* ANALYZE */}

              <button
                type="button"
                className="analyze-button"
                onClick={
                  handleAnalyzeVoyage
                }
              >

                Analyze Voyage

                <ArrowRight size={17} />

              </button>

            </div>

          </section>


          {/* KPI */}

          <section className="metrics-grid">


            <div className="metric-card">

              <div className="metric-icon blue">
                <Database size={27} />
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
                <BarChart3 size={52} />
              </div>

            </div>


            <div className="metric-card">

              <div className="metric-icon green">
                <CalendarDays size={27} />
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
                <CalendarDays size={48} />
              </div>

            </div>


            <div className="metric-card">

              <div className="metric-icon emerald">
                <ShieldCheck size={28} />
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
                <BarChart3 size={50} />
              </div>

            </div>


            <div className="metric-card">

              <div className="metric-icon sky">
                <CircleDollarSign size={27} />
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
                <BarChart3 size={52} />
              </div>

            </div>

          </section>


          {/* =================================================
              ANALYTICS
          ================================================= */}

          <section className="analytics-grid">


            {/* FREIGHT */}

            <div className="panel freight-panel">

              <div className="panel-header">

                <div>

                  <h3>
                    <BarChart3 size={18} />
                    Freight Rate Trend
                  </h3>

                  <span>
                    Freight Rate (USD/MT)
                  </span>

                </div>


                <div className="range-buttons">

                  {[
                    "7 Days",
                    "14 Days",
                    "30 Days",
                  ].map((item) => (

                    <button
                      type="button"
                      key={item}
                      className={
                        range === item
                          ? "selected"
                          : ""
                      }
                      onClick={() =>
                        handleRangeChange(item)
                      }
                    >
                      {item}
                    </button>

                  ))}

                </div>

              </div>


              <div className="chart-container">

                <FreightChart
                  selectedRange={range}
                  navigationIndex={
                    navigationIndex
                  }
                />

              </div>

            </div>


            {/* PORTS */}

            <div className="panel port-panel">

              <div className="panel-header">

                <h3>
                  <Anchor size={18} />
                  East Coast Port Status
                </h3>


                <Link
                  to="/ports"
                  className="view-link"
                >
                  View All Ports
                  <ArrowRight size={12} />
                </Link>

              </div>


              <div className="port-table">

                <div className="port-row table-heading">

                  <span>Port</span>

                  <span>Status</span>

                  <span>
                    Avg. Waiting Time
                  </span>

                  <span>
                    Trend (7 days)
                  </span>

                </div>


                {portData.map((port) => (

                  <div
                    className="port-row"
                    key={port.name}
                  >

                    <div className="port-name">

                      <Anchor size={13} />

                      {port.name}

                    </div>


                    <div
                      className={
                        `port-status ${port.statusClass}`
                      }
                    >

                      <i />

                      {port.status}

                    </div>


                    <span>
                      {port.waiting}
                    </span>


                    <PortTrend
                      direction={port.trend}
                    />

                  </div>

                ))}

              </div>

            </div>


            {/* VOYAGES */}

            <div className="panel voyages-panel">

              <div className="panel-header">

                <h3>
                  <Ship size={18} />
                  Recent Voyages
                </h3>


                <Link
                  to="/new-voyage"
                  className="view-link"
                >
                  View All
                  <ArrowRight size={12} />
                </Link>

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
                        <Ship size={17} />
                      </div>

                      {voyage.id}

                    </div>


                    <span>
                      {voyage.cargo}
                    </span>


                    <span>
                      {voyage.route}
                    </span>


                    <span
                      className={
                        `voyage-status ${voyage.statusClass}`
                      }
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
                <Lightbulb size={29} />
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
                  Freight rates are expected to
                  decline over the next 10 days.
                  FreightWise suggests monitoring
                  the current market before locking
                  a vessel.
                </p>


                <ul>

                  <li>
                    Declining trend in global coal
                    freight rates
                  </li>

                  <li>
                    Lower congestion expected
                    at Paradip
                  </li>

                  <li>
                    Favourable weather conditions
                    in Bay of Bengal
                  </li>

                </ul>

              </div>


              <div className="insight-graph">
                <BarChart3 size={88} />
              </div>

            </div>

          </section>

        </div>

      </main>

    </div>
  );
}