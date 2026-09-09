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
  ShipWheel,
  CheckCircle2,
} from "lucide-react";

import oceanStar from "../../assets/images/vessel-ocean-star.png";
import stella from "../../assets/images/vessel-stella.png";
import horizon from "../../assets/images/vessel-horizon.png";
import pacificGlory from "../../assets/images/vessel-pacific-glory.png";

import VesselCard from "../../components/vessels/VesselCard";
import VesselTable from "../../components/vessels/VesselTable";

import {
  FitBadge,
  AvailabilityBadge,
} from "../../components/vessels/CompatibilityBadge";

import "./Vessels.css";

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
  window.dispatchEvent(
    new PopStateEvent("popstate")
  );
}

function Sidebar() {
  return (
    <aside className="vessels-sidebar">

      <div className="sidebar-brand">

        <div className="sidebar-logo">
          <Ship
            size={35}
            strokeWidth={2}
          />
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
          const active =
            item.label === "Vessels";

          return (
            <button
              key={item.label}
              className={`sidebar-nav-item ${
                active ? "active" : ""
              }`}
              onClick={() =>
                navigateTo(item.path)
              }
            >
              <Icon
                size={21}
                strokeWidth={2}
              />

              <span>
                {item.label}
              </span>
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

          <span className="user-avatar">
            K
          </span>

          <span>
            User
          </span>

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

      <label>
        {label}
      </label>

      <div className="filter-select-wrapper">

        <select
          value={value}
          onChange={onChange}
        >
          {options.map((option) => (
            <option
              key={option}
              value={option}
            >
              {option}
            </option>
          ))}
        </select>

        <ChevronDown size={15} />

      </div>

    </div>
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

  const [selectedVessel, setSelectedVessel] =
    useState(null);

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

      if (
        dwtRange ===
        "50,000 - 100,000"
      ) {
        dwtMatch =
          vessel.dwt >= 50000 &&
          vessel.dwt <= 100000;
      }

      if (
        dwtRange ===
        "60,000 - 80,000"
      ) {
        dwtMatch =
          vessel.dwt >= 60000 &&
          vessel.dwt <= 80000;
      }

      if (
        dwtRange ===
        "80,000 - 100,000"
      ) {
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

              <h1>
                Recommended Vessels
              </h1>

              <p>
                Best matching vessels for your cargo and route
              </p>

            </div>

            <div className="fleet-banner">

              <div className="fleet-banner-overlay">

                <strong>
                  Global Fleet.
                </strong>

                <span>
                  Smarter Choices.
                </span>

                <span>
                  Brighter Voyages.
                </span>

              </div>

            </div>

          </section>


          {/* FILTERS */}

          <section className="filters-card">

            <FilterSelect
              label="Vessel Type"
              value={vesselType}
              onChange={(e) =>
                setVesselType(
                  e.target.value
                )
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
                setDwtRange(
                  e.target.value
                )
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
                setAvailability(
                  e.target.value
                )
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
                setCargoFit(
                  e.target.value
                )
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
                setPortFit(
                  e.target.value
                )
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
                  onViewDetails={
                    setSelectedVessel
                  }
                />
              ))}

          </section>


          {/* ALL VESSELS */}

          <VesselTable
            vessels={filteredVessels}
            onViewDetails={
              setSelectedVessel
            }
          />


          {/* VESSEL DETAILS MODAL */}

          {selectedVessel && (

            <div
              className="vessel-details-overlay"
              onClick={() =>
                setSelectedVessel(null)
              }
            >

              <div
                className="vessel-details-modal"
                onClick={(e) =>
                  e.stopPropagation()
                }
              >

                <button
                  className="vessel-details-close"
                  onClick={() =>
                    setSelectedVessel(null)
                  }
                  aria-label="Close vessel details"
                >
                  ×
                </button>


                {/* IMAGE */}

                <div className="vessel-details-image">

                  <img
                    src={selectedVessel.image}
                    alt={`${selectedVessel.name} bulk carrier`}
                  />

                  {selectedVessel.recommended && (
                    <div className="details-recommended-badge">

                      <CheckCircle2
                        size={14}
                      />

                      AI Recommended

                    </div>
                  )}

                </div>


                {/* DETAILS */}

                <div className="vessel-details-content">

                  <div className="vessel-details-heading">

                    <div>

                      <h2>
                        {selectedVessel.name}
                      </h2>

                      <p>
                        {selectedVessel.dwt.toLocaleString()} DWT
                        <span>
                          |
                        </span>
                        {selectedVessel.type}
                      </p>

                    </div>

                    <AvailabilityBadge
                      value={
                        selectedVessel.availability
                      }
                    />

                  </div>


                  {/* COMPATIBILITY */}

                  <div className="vessel-details-grid">

                    <div className="detail-item">

                      <span>
                        Cargo Fit
                      </span>

                      <FitBadge
                        value={
                          selectedVessel.cargoFit
                        }
                      />

                    </div>


                    <div className="detail-item">

                      <span>
                        Port Fit
                      </span>

                      <FitBadge
                        value={
                          selectedVessel.portFit
                        }
                      />

                    </div>


                    <div className="detail-item">

                      <span>
                        Availability
                      </span>

                      <AvailabilityBadge
                        value={
                          selectedVessel.availability
                        }
                      />

                    </div>


                    <div className="detail-item">

                      <span>
                        Deadweight
                      </span>

                      <strong>
                        {selectedVessel.dwt.toLocaleString()} DWT
                      </strong>

                    </div>

                  </div>


                  {/* COST */}

                  <div className="vessel-cost-details">

                    <div>

                      <span>
                        Estimated Voyage Cost
                      </span>

                      <strong>
                        ₹ {selectedVessel.cost.toFixed(2)} Cr
                      </strong>

                    </div>

                    <div>

                      <span>
                        Freight Cost
                      </span>

                      <strong>
                        ${selectedVessel.costPerMt.toFixed(1)} / MT
                      </strong>

                    </div>

                  </div>


                  {/* AI NOTE */}

                  {selectedVessel.recommended && (

                    <div className="vessel-ai-note">

                      <CheckCircle2
                        size={17}
                      />

                      <div>

                        <strong>
                          AI Recommendation
                        </strong>

                        <p>
                          This vessel is currently
                          identified as a recommended
                          match for the selected cargo
                          and route.
                        </p>

                      </div>

                    </div>

                  )}

                </div>

              </div>

            </div>

          )}

        </div>

      </main>

    </div>
  );
}