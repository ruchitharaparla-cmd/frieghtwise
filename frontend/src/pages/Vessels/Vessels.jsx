import React, { useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  Home,
  Ship,
  BarChart3,
  MapPin,
  RotateCcw,
  Settings,
  ArrowRight,
  Star,
  CheckCircle2,
  XCircle,
  Navigation,
  ShipWheel,
} from "lucide-react";

import "./Vessels.css";

import oceanStar from "../../assets/images/vessel-ocean-star.png";
import stella from "../../assets/images/vessel-stella.png";
import horizon from "../../assets/images/vessel-horizon.png";
import pacificGlory from "../../assets/images/vessel-pacific-glory.png";

const vesselData = [
  {
    id: 1,
    name: "MV Ocean Star",
    dwt: 76000,
    type: "Bulk Carrier",
    cargoFit: "Excellent",
    portFit: "Good",
    availability: "Available",
    cost: 6.42,
    costPerMt: 24.8,
    image: oceanStar,
    recommended: true,
  },
  {
    id: 2,
    name: "MV Stella",
    dwt: 80000,
    type: "Bulk Carrier",
    cargoFit: "Good",
    portFit: "Moderate",
    availability: "Available",
    cost: 6.38,
    costPerMt: 23.6,
    image: stella,
  },
  {
    id: 3,
    name: "MV Horizon",
    dwt: 70000,
    type: "Bulk Carrier",
    cargoFit: "Moderate",
    portFit: "Good",
    availability: "In Positioning",
    cost: 6.71,
    costPerMt: 22.5,
    image: horizon,
  },
  {
    id: 4,
    name: "MV Pacific Glory",
    dwt: 82000,
    type: "Bulk Carrier",
    cargoFit: "Good",
    portFit: "Good",
    availability: "Available",
    cost: 6.55,
    costPerMt: 24.1,
    image: pacificGlory,
  },
  {
    id: 5,
    name: "MV Eastern Wind",
    dwt: 75000,
    type: "Bulk Carrier",
    cargoFit: "Moderate",
    portFit: "Moderate",
    availability: "Available",
    cost: 6.68,
    costPerMt: 24.6,
    image: oceanStar,
  },
  {
    id: 6,
    name: "MV Sea Voyager",
    dwt: 68000,
    type: "Bulk Carrier",
    cargoFit: "Good",
    portFit: "Moderate",
    availability: "Unavailable",
    cost: 6.80,
    costPerMt: 25.0,
    image: stella,
  },
  {
    id: 7,
    name: "MV Blue Horizon",
    dwt: 77000,
    type: "Bulk Carrier",
    cargoFit: "Good",
    portFit: "Good",
    availability: "Available",
    cost: 6.45,
    costPerMt: 24.2,
    image: horizon,
  },
  {
    id: 8,
    name: "MV Coral Star",
    dwt: 83000,
    type: "Bulk Carrier",
    cargoFit: "Moderate",
    portFit: "Good",
    availability: "Available",
    cost: 6.73,
    costPerMt: 24.7,
    image: pacificGlory,
  },
];

const navItems = [
  {
    label: "Dashboard",
    icon: Home,
    path: "/",
  },
  {
    label: "New Voyage",
    icon: Ship,
    path: "/new-voyage",
  },
  {
    label: "Analysis",
    icon: BarChart3,
    path: "/analysis",
  },
  {
    label: "Vessels",
    icon: ShipWheel,
    path: "/vessels",
  },
  {
    label: "Ports",
    icon: MapPin,
    path: "/ports",
  },
  {
    label: "Simulation",
    icon: RotateCcw,
    path: "/simulation",
  },
  {
    label: "Settings",
    icon: Settings,
    path: "/settings",
  },
];

function navigateTo(path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function FitBadge({ value }) {
  const className =
    value === "Excellent"
      ? "fit-excellent"
      : value === "Good"
        ? "fit-good"
        : "fit-moderate";

  return (
    <span className={`fit-badge ${className}`}>
      <CheckCircle2 size={12} />
      {value}
    </span>
  );
}

function AvailabilityBadge({ value }) {
  let icon = <CheckCircle2 size={12} />;
  let className = "availability-available";

  if (value === "In Positioning") {
    icon = <Navigation size={12} />;
    className = "availability-positioning";
  }

  if (value === "Unavailable") {
    icon = <XCircle size={12} />;
    className = "availability-unavailable";
  }

  return (
    <span className={`availability-badge ${className}`}>
      {icon}
      {value}
    </span>
  );
}

function Sidebar() {
  return (
    <aside className="vessels-sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <Ship size={35} strokeWidth={2} />
        </div>

        <div className="sidebar-brand-name">
          FREIGHTWISE
        </div>

        <div className="sidebar-tagline">
          Navigate Smarter.
          <br />
          Charter Better.
        </div>
      </div>

      <nav className="sidebar-navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = item.label === "Vessels";

          return (
            <button
              key={item.label}
              className={`sidebar-nav-item ${
                active ? "active" : ""
              }`}
              onClick={() => navigateTo(item.path)}
            >
              <Icon size={21} strokeWidth={2} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <div className="ai-status">
          <div className="ai-status-title">
            <span className="online-indicator" />
            AI Engine Online
          </div>

          <div className="ai-status-text">
            Data updated
          </div>

          <div className="ai-status-time">
            2 min ago
          </div>
        </div>

        <div className="sidebar-waves">
          <span />
          <span />
        </div>

        <p className="sidebar-quote">
          “Right Vessels.
          <br />
          Lower Costs.
          <br />
          A Stronger India.”
        </p>
      </div>
    </aside>
  );
}

function Topbar() {
  return (
    <header className="vessels-topbar">
      <div className="global-search">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search vessels, ports, routes..."
        />
      </div>

      <div className="topbar-right">
        <div className="topbar-divider" />

        <button className="notification-button">
          <Bell size={23} />

          <span className="notification-count">
            3
          </span>
        </button>

        <div className="topbar-divider" />

        <button className="user-button">
          <span className="user-avatar">K</span>

          <span>User</span>

          <ChevronDown size={16} />
        </button>
      </div>
    </header>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}) {
  return (
    <div className="filter-field">
      <label>{label}</label>

      <div className="filter-select-wrapper">
        <select value={value} onChange={onChange}>
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>

        <ChevronDown size={15} />
      </div>
    </div>
  );
}

function VesselCard({ vessel }) {
  return (
    <article
      className={`vessel-card ${
        vessel.recommended ? "recommended-card" : ""
      }`}
    >
      <div className="vessel-card-image">
        <img
          src={vessel.image}
          alt={`${vessel.name} bulk carrier`}
        />

        {vessel.recommended && (
          <div className="ai-recommended">
            <CheckCircle2 size={13} />
            AI Recommended
          </div>
        )}

        {vessel.recommended && (
          <button
            className="favorite-button"
            aria-label="Favorite vessel"
          >
            <Star
              size={18}
              fill="currentColor"
            />
          </button>
        )}
      </div>

      <div className="vessel-card-body">
        <div className="vessel-card-title">
          <h3>{vessel.name}</h3>

          <p>
            {vessel.dwt.toLocaleString()} DWT
            <span>|</span>
            {vessel.type}
          </p>
        </div>

        <div className="vessel-card-details">
          <div className="fit-section">
            <div className="fit-row">
              <span>Cargo Fit</span>
              <FitBadge value={vessel.cargoFit} />
            </div>

            <div className="fit-row">
              <span>Port Fit</span>
              <FitBadge value={vessel.portFit} />
            </div>

            <div className="fit-row">
              <span>Availability</span>
              <AvailabilityBadge
                value={vessel.availability}
              />
            </div>
          </div>

          <div className="estimated-cost">
            <span>Est. Cost</span>

            <strong>
              ₹ {vessel.cost.toFixed(2)} Cr
            </strong>

            <small>
              (${vessel.costPerMt.toFixed(1)} / MT)
            </small>
          </div>
        </div>

        <button className="view-details-link">
          View Details
          <ArrowRight size={15} />
        </button>
      </div>
    </article>
  );
}

export default function Vessels() {
  const [vesselType, setVesselType] =
    useState("All Types");

  const [dwtRange, setDwtRange] =
    useState("50,000 - 100,000");

  const [availability, setAvailability] =
    useState("Available");

  const [cargoFit, setCargoFit] =
    useState("All");

  const [portFit, setPortFit] =
    useState("All");

  const filteredVessels = useMemo(() => {
    return vesselData.filter((vessel) => {
      const typeMatch =
        vesselType === "All Types" ||
        vessel.type === vesselType;

      const availabilityMatch =
        availability === "All" ||
        vessel.availability === availability;

      const cargoMatch =
        cargoFit === "All" ||
        vessel.cargoFit === cargoFit;

      const portMatch =
        portFit === "All" ||
        vessel.portFit === portFit;

      let dwtMatch = true;

      if (dwtRange === "50,000 - 100,000") {
        dwtMatch =
          vessel.dwt >= 50000 &&
          vessel.dwt <= 100000;
      }

      if (dwtRange === "60,000 - 80,000") {
        dwtMatch =
          vessel.dwt >= 60000 &&
          vessel.dwt <= 80000;
      }

      if (dwtRange === "80,000 - 100,000") {
        dwtMatch =
          vessel.dwt >= 80000 &&
          vessel.dwt <= 100000;
      }

      return (
        typeMatch &&
        availabilityMatch &&
        cargoMatch &&
        portMatch &&
        dwtMatch
      );
    });
  }, [
    vesselType,
    dwtRange,
    availability,
    cargoFit,
    portFit,
  ]);

  function clearFilters() {
    setVesselType("All Types");
    setDwtRange("50,000 - 100,000");
    setAvailability("Available");
    setCargoFit("All");
    setPortFit("All");
  }

  return (
    <div className="vessels-page">
      <Sidebar />

      <main className="vessels-main">
        <Topbar />

        <div className="vessels-content">

          {/* PAGE HEADER */}
          <section className="vessels-page-header">
            <div>
              <h1>Recommended Vessels</h1>

              <p>
                Best matching vessels for your cargo and route
              </p>
            </div>

            <div className="fleet-banner">
              <div className="fleet-banner-overlay">
                <strong>Global Fleet.</strong>
                <span>Smarter Choices.</span>
                <span>Brighter Voyages.</span>
              </div>
            </div>
          </section>

          {/* FILTERS */}
          <section className="filters-card">
            <FilterSelect
              label="Vessel Type"
              value={vesselType}
              onChange={(e) =>
                setVesselType(e.target.value)
              }
              options={[
                "All Types",
                "Bulk Carrier",
              ]}
            />

            <FilterSelect
              label="DWT Range"
              value={dwtRange}
              onChange={(e) =>
                setDwtRange(e.target.value)
              }
              options={[
                "50,000 - 100,000",
                "60,000 - 80,000",
                "80,000 - 100,000",
                "All",
              ]}
            />

            <FilterSelect
              label="Availability"
              value={availability}
              onChange={(e) =>
                setAvailability(e.target.value)
              }
              options={[
                "Available",
                "All",
                "In Positioning",
                "Unavailable",
              ]}
            />

            <FilterSelect
              label="Cargo Fit"
              value={cargoFit}
              onChange={(e) =>
                setCargoFit(e.target.value)
              }
              options={[
                "All",
                "Excellent",
                "Good",
                "Moderate",
              ]}
            />

            <FilterSelect
              label="Port Fit"
              value={portFit}
              onChange={(e) =>
                setPortFit(e.target.value)
              }
              options={[
                "All",
                "Excellent",
                "Good",
                "Moderate",
              ]}
            />

            <div className="filter-buttons">
              <button
                className="clear-filters-button"
                onClick={clearFilters}
              >
                Clear Filters
              </button>

              <button className="search-vessels-button">
                <Search size={16} />
                Search
              </button>
            </div>
          </section>

          {/* RECOMMENDED CARDS */}
          <section className="recommended-grid">
            {filteredVessels
              .slice(0, 3)
              .map((vessel) => (
                <VesselCard
                  key={vessel.id}
                  vessel={vessel}
                />
              ))}
          </section>

          {/* ALL VESSELS */}
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
                    {filteredVessels.length}
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
                  {filteredVessels.map((vessel) => (
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

                      <td>{vessel.type}</td>

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
                          value={
                            vessel.availability
                          }
                        />
                      </td>

                      <td>
                        <div className="table-cost">
                          <strong>
                            ₹ {vessel.cost.toFixed(2)} Cr
                          </strong>

                          <span>
                            (${vessel.costPerMt.toFixed(1)} / MT)
                          </span>
                        </div>
                      </td>

                      <td>
                        <button className="table-details-button">
                          View Details
                        </button>
                      </td>

                    </tr>
                  ))}
                </tbody>

              </table>
            </div>

          </section>

        </div>
      </main>
    </div>
  );
}