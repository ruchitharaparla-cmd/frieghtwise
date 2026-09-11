import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

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
import { getVessels, getPorts } from "../../services/api";

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

function Sidebar() {
  const navigate = useNavigate();

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
              type="button"
              key={item.label}
              className={`sidebar-nav-item ${
                active ? "active" : ""
              }`}
              onClick={() => navigate(item.path)}
            >
              <Icon
                size={21}
                strokeWidth={2}
              />

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

function Topbar({ searchText, setSearchText, onSearch }) {
  return (
    <header className="vessels-topbar">
      <div className="global-search">
        <Search size={18} />

        <input
          type="text"
          placeholder="Search vessels, ports, routes..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              onSearch();
            }
          }}
        />
      </div>

      <div className="topbar-right">
        <div className="topbar-divider" />

        <button
          type="button"
          className="notification-button"
        >
          <Bell size={23} />

          <span className="notification-count">
            3
          </span>
        </button>

        <div className="topbar-divider" />

        <button
          type="button"
          className="user-button"
        >
          <span className="user-avatar">
            K
          </span>

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
  const [vesselData, setVesselData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");

  useEffect(() => {
    async function loadVessels() {
      try {
        const [vesselResponse, portResponse] =
          await Promise.all([
            getVessels(),
            getPorts(),
          ]);

        const apiVessels = Array.isArray(
          vesselResponse?.vessels
        )
          ? vesselResponse.vessels
          : Array.isArray(vesselResponse)
          ? vesselResponse
          : [];

        const apiPorts = Array.isArray(
          portResponse?.ports
        )
          ? portResponse.ports
          : Array.isArray(portResponse)
          ? portResponse
          : [];

        const getCargoFit = (vesselClass) => {
          const type = String(
            vesselClass || ""
          ).toLowerCase();

          if (type.includes("bulk")) {
            return "Excellent";
          }

          if (type.includes("tanker")) {
            return "Good";
          }

          return "Moderate";
        };

        const getPortFit = (vessel) => {
          const compatiblePorts =
            apiPorts.filter((port) => {
              const draftOk =
                port.max_draft_m == null ||
                vessel.draft_m == null ||
                Number(vessel.draft_m) <=
                  Number(port.max_draft_m);

              const loaOk =
                port.max_loa_m == null ||
                vessel.loa_m == null ||
                Number(vessel.loa_m) <=
                  Number(port.max_loa_m);

              const beamOk =
                port.max_beam_m == null ||
                vessel.beam_m == null ||
                Number(vessel.beam_m) <=
                  Number(port.max_beam_m);

              return (
                draftOk &&
                loaOk &&
                beamOk
              );
            });

          if (compatiblePorts.length === 0) {
            return "Unavailable";
          }

          if (compatiblePorts.length >= 10) {
            return "Excellent";
          }

          if (compatiblePorts.length >= 5) {
            return "Good";
          }

          return "Moderate";
        };

        const normalized = apiVessels.map(
          (vessel, index) => ({
            id: vessel.id,
            name:
              vessel.name ||
              "Name unavailable",

            dwt:
              Number(vessel.dwt) || 0,

            type:
              vessel.vessel_class ||
              "Type unavailable",

            cargoFit:
              getCargoFit(
                vessel.vessel_class
              ),

            portFit:
              getPortFit(vessel),

            availability:
              "Unavailable",

            cost: null,
            costPerMt: null,

            image: [
              oceanStar,
              stella,
              horizon,
              pacificGlory,
            ][index % 4],

            recommended: false,

            loa: vessel.loa_m,
            beam: vessel.beam_m,
            draft: vessel.draft_m,
          })
        );

        setVesselData(normalized);
      } catch (error) {
        console.error(
          "Failed to load vessels:",
          error
        );

        setVesselData([]);
      } finally {
        setLoading(false);
      }
    }

    loadVessels();
  }, []);

  const [vesselType, setVesselType] =
    useState("All Types");

  const [dwtRange, setDwtRange] =
    useState("50,000 - 100,000");

  const [availability, setAvailability] =
    useState("All");

  const [cargoFit, setCargoFit] =
    useState("All");

  const [portFit, setPortFit] =
    useState("All");

  const [selectedVessel, setSelectedVessel] =
    useState(null);

  const filteredVessels = useMemo(() => {
    return vesselData.filter((vessel) => {
      const searchMatch =
        !appliedSearch ||
        vessel.name
          .toLowerCase()
          .includes(appliedSearch.toLowerCase()) ||
        vessel.type
          .toLowerCase()
          .includes(appliedSearch.toLowerCase());

      const typeMatch =
        vesselType === "All Types" ||
        vessel.type === vesselType;

      const availabilityMatch =
        availability === "All" ||
        vessel.availability ===
          availability ||
        vessel.availability ===
          "Unavailable";

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
        searchMatch &&
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
    appliedSearch,
  ]);

  function clearFilters() {
    setVesselType("All Types");
    setDwtRange("50,000 - 100,000");
    setAvailability("All");
    setCargoFit("All");
    setPortFit("All");
  }

  return (
    <div className="vessels-page">
      <Sidebar />

      <main className="vessels-main">
        <Topbar
          searchText={searchText}
          setSearchText={setSearchText}
          onSearch={() => setAppliedSearch(searchText.trim())}
        />

        <div className="vessels-content">
          {/* PAGE HEADER */}
          <section className="vessels-page-header">
            <div>
              <h1>
                Recommended Vessels
              </h1>

              <p>
                Best matching vessels for
                your cargo and route
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
                ...Array.from(
                  new Set(
                    vesselData.map(
                      (v) => v.type
                    )
                  )
                ).filter(Boolean),
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
                type="button"
                className="clear-filters-button"
                onClick={clearFilters}
              >
                Clear Filters
              </button>

              <button
                type="button"
                className="search-vessels-button"
                onClick={() => {
                  setAppliedSearch(searchText.trim());
                }}
              >
                <Search size={16} />
                Search
              </button>
            </div>
          </section>

          {/* LOADING */}
          {loading && (
            <div className="vessels-loading">
              Loading vessels from backend...
            </div>
          )}

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
                  type="button"
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
                    src={
                      selectedVessel.image
                    }
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
                        {
                          selectedVessel.name
                        }
                      </h2>

                      <p>
                        {selectedVessel.dwt.toLocaleString()}{" "}
                        DWT
                        <span>|</span>
                        {
                          selectedVessel.type
                        }
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
                        {selectedVessel.dwt.toLocaleString()}{" "}
                        DWT
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
                        {typeof selectedVessel.cost ===
                        "number"
                          ? `₹ ${selectedVessel.cost.toFixed(
                              2
                            )} Cr`
                          : "Unavailable"}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Freight Cost
                      </span>

                      <strong>
                        {typeof selectedVessel.costPerMt ===
                        "number"
                          ? `$${selectedVessel.costPerMt.toFixed(
                              1
                            )} / MT`
                          : "Unavailable"}
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
                          This vessel is
                          currently identified
                          as a recommended
                          match for the selected
                          cargo and route.
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