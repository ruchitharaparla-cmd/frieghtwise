import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Anchor,
  BarChart3,
  Bell,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Home,
  Info,
  MapPin,
  Menu,
  Navigation,
  Play,
  Settings,
  ShieldCheck,
  Ship,
  Sparkles,
  UserRound,
} from "lucide-react";

import "./Simulation.css";
import simulImage from "../../assets/images/simul.png";
import { runSimulation as runSimulationApi, getVessels, getPorts } from "../../services/api";

const scenarios = [
  {
    id: "now",
    title: "Charter Now",
    date: "12 – 18 Sep 2026",
    rate: "$24.8 / MT",
    cost: "₹6.42 Cr",
    risk: "Low",
    delay: "2.4 Days",
    type: "low",
    recommended: true,
    message:
      "Best balance of cost and risk for current market conditions.",
  },
  {
    id: "7",
    title: "Wait 7 Days",
    date: "19 – 25 Sep 2026",
    rate: "$23.6 / MT",
    cost: "₹6.38 Cr",
    risk: "Moderate",
    delay: "3.8 Days",
    type: "moderate",
    recommended: false,
    message:
      "Slightly lower freight rate, but higher risk of congestion and weather impact.",
  },
  {
    id: "14",
    title: "Wait 14 Days",
    date: "26 Sep – 2 Oct 2026",
    rate: "$22.5 / MT",
    cost: "₹6.71 Cr",
    risk: "High",
    delay: "5.6 Days",
    type: "high",
    recommended: false,
    message:
      "Lower freight rate but significantly higher risk and total cost due to expected delays.",
  },
];

function Simulation() {
  const navigate = useNavigate();

  const [charteringDate, setCharteringDate] = useState("2026-09-12");
  const [waitingPeriod, setWaitingPeriod] = useState("7");
  const [vessel, setVessel] = useState("");
  const [route, setRoute] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [running, setRunning] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);
  const [simulationError, setSimulationError] = useState("");
  const [vessels, setVessels] = useState([]);
  const [ports, setPorts] = useState([]);

  useEffect(() => {
    async function loadOptions() {
      try {
        const [vesselResponse, portResponse] = await Promise.all([
          getVessels(),
          getPorts(),
        ]);

        setVessels(vesselResponse?.vessels || vesselResponse || []);
        setPorts(portResponse?.ports || portResponse || []);
      } catch {
        setVessels([]);
        setPorts([]);
      }
    }

    loadOptions();
  }, []);

  const getVoyageInput = () => {
    try {
      const stored = sessionStorage.getItem("freightwise_voyage_input");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  };

  const addDays = (dateString, days) => {
    const date = new Date(`${dateString}T00:00:00`);
    date.setDate(date.getDate() + Number(days || 0));
    return date.toISOString().slice(0, 10);
  };

  const findPortId = () => {
    const destination = route.split("→").pop()?.trim().toLowerCase();

    const match = ports.find((port) => {
      const name = String(port.name || "").toLowerCase();
      return name.includes(destination) || destination.includes(name);
    });

    return match?.id ?? null;
  };

  const findVesselClass = () => {
    const match = vessels.find(
      (item) =>
        String(item.name || "").toLowerCase() ===
        String(vessel || "").toLowerCase()
    );

    return match?.vessel_class ?? null;
  };

  const runSimulation = async () => {
    setRunning(true);
    setCompleted(false);
    setSimulationError("");

    try {
      const voyage = getVoyageInput();

      if (!voyage) {
        throw new Error(
          "Voyage input is unavailable. Please create a voyage first."
        );
      }

      const baseScenario = {
        cargo_type: voyage.cargoType,
        quantity_tonnes: Number(voyage.quantity),
        origin_country:
          voyage.loadingPort?.split(",").pop()?.trim() || "",
        destination_region: "East Coast India",
        arrival_date: voyage.arrivalDate,
      };

      const response = await runSimulationApi({
        base_scenario: baseScenario,
        changes: {
          charter_duration_days: Number(waitingPeriod) || undefined,
          vessel_id: vessel ? Number(vessel) : undefined,
          port_id: route ? Number(route) : undefined,
        },
      });

      setSimulationResult(response);
      setCompleted(true);
    } catch (error) {
      setSimulationResult(null);
      setSimulationError(error.message || "Simulation failed.");
      setCompleted(false);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="freightwise-layout">
      {/* =====================================================
          SIDEBAR
      ====================================================== */}
      <aside
        className={`freight-sidebar ${
          sidebarOpen ? "sidebar-open" : "sidebar-closed"
        }`}
      >
        <div className="sidebar-brand">
          <div className="brand-logo">
            <Anchor size={42} strokeWidth={2} />
          </div>

          <div className="brand-name">FREIGHTWISE</div>

          <div className="brand-tagline">
            Navigate Smarter.
            <br />
            Charter Better.
          </div>
        </div>

        <nav className="sidebar-navigation">
          <button
            className="sidebar-item"
            onClick={() => navigate("/")}
          >
            <Home size={23} />
            <span>Dashboard</span>
          </button>

          <button
            className="sidebar-item"
            onClick={() => navigate("/new-voyage")}
          >
            <Navigation size={23} />
            <span>New Voyage</span>
          </button>

          <button
            className="sidebar-item"
            onClick={() => navigate("/analysis")}
          >
            <BarChart3 size={23} />
            <span>Analysis</span>
          </button>

          <button
            className="sidebar-item"
            onClick={() => navigate("/vessels")}
          >
            <Ship size={23} />
            <span>Vessels</span>
          </button>

          <button
            className="sidebar-item"
            onClick={() => navigate("/ports")}
          >
            <MapPin size={23} />
            <span>Ports</span>
          </button>

          <button className="sidebar-item active">
            <Sparkles size={23} />
            <span>Simulation</span>
          </button>

          <button
            className="sidebar-item"
            onClick={() => navigate("/settings")}
          >
            <Settings size={23} />
            <span>Settings</span>
          </button>
        </nav>

        {/* AI ENGINE STATUS */}
        <div className="ai-engine-card">
          <div className="ai-status-title">
            <span className="online-dot" />
            <span>AI Engine Online</span>
          </div>

          <div className="ai-updated">Data updated</div>

          <strong>2 min ago</strong>
        </div>

        <div className="sidebar-quote">
          “Better Decisions
          <br />
          Today.
          <br />
          Smoother Voyages
          <br />
          Tomorrow.”
        </div>
      </aside>

      {/* =====================================================
          MAIN AREA
      ====================================================== */}
      <div className="freight-main">
        {/* ===================================================
            TOP BAR
        ==================================================== */}
        <header className="freight-topbar">
          <button
            className="mobile-menu-button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <Menu size={22} />
          </button>

          <div className="global-search">
            <svg
              width="19"
              height="19"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-4-4" />
            </svg>

            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />
          </div>

          <div className="topbar-right">
            <button className="notification-button">
              <Bell size={25} />

              <span className="notification-count">3</span>
            </button>

            <div className="topbar-divider" />

            <div className="user-profile">
              <div className="user-avatar">K</div>

              <span>User</span>

              <ChevronDown size={17} />
            </div>
          </div>
        </header>

        {/* ===================================================
            PAGE CONTENT
        ==================================================== */}
        <main className="simulation-content">
          {/* HERO */}
          <section className="simulation-hero">
            <div className="simulation-hero-content">
              <span className="hero-eyebrow">
                FREIGHTWISE SIMULATION ENGINE
              </span>

              <h1>What-If Analysis</h1>

              <p>
                Compare different chartering windows and scenarios
              </p>
            </div>

            <img
              src={simulImage}
              alt="Cargo ship at port"
              className="simulation-hero-ship"
            />

            <div className="simulation-hero-slogan">
              <strong>Simulate Today.</strong>

              <strong>Sail Smarter</strong>

              <strong>Tomorrow.</strong>

              <span />
            </div>
          </section>

          {/* =================================================
              PARAMETERS
          ================================================== */}
          <section className="parameters-card">
            <div className="parameters-heading">
              <div className="parameters-icon">
                <Settings size={27} />
              </div>

              <div>
                <h2>Simulation Parameters</h2>

                <p>
                  Adjust the inputs to compare different scenarios
                </p>
              </div>
            </div>

            <div className="parameter-grid">
              {/* DATE */}
              <div className="parameter-field">
                <label>Chartering Date</label>

                <div className="input-wrapper">
                  <CalendarDays size={19} />

                  <input
                    type="date"
                    value={charteringDate}
                    onChange={(e) =>
                      setCharteringDate(e.target.value)
                    }
                  />
                </div>
              </div>

              {/* WAITING PERIOD */}
              <div className="parameter-field">
                <label>Waiting Period</label>

                <div className="select-wrapper">
                  <Clock3 size={19} />

                  <select
                    value={waitingPeriod}
                    onChange={(e) =>
                      setWaitingPeriod(e.target.value)
                    }
                  >
                    <option value="0">Charter Now</option>

                    <option value="7">Wait 7 Days</option>

                    <option value="14">Wait 14 Days</option>

                    <option value="21">Wait 21 Days</option>
                  </select>

                  <ChevronDown
                    size={18}
                    className="select-arrow"
                  />
                </div>
              </div>

              {/* VESSEL */}
              <div className="parameter-field">
                <label>Vessel Option</label>

                <div className="select-wrapper">
                  <Ship size={19} />

                  <select
                    value={vessel}
                    onChange={(e) => setVessel(e.target.value)}
                  >
                    {vessels.length > 0 ? (
                      vessels.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))
                    ) : (
                      <option value="">No vessels available</option>
                    )}
                  </select>

                  <ChevronDown
                    size={18}
                    className="select-arrow"
                  />
                </div>
              </div>

              {/* ROUTE */}
              <div className="parameter-field">
                <label>Route / Port Option</label>

                <div className="select-wrapper">
                  <MapPin size={19} />

                  <select
                    value={route}
                    onChange={(e) => setRoute(e.target.value)}
                  >
                    {ports.length > 0 ? (
                      ports.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))
                    ) : (
                      <option value="">No ports available</option>
                    )}
                  </select>

                  <ChevronDown
                    size={18}
                    className="select-arrow"
                  />
                </div>
              </div>

              {/* RUN BUTTON */}
              <button
                className="run-simulation-button"
                onClick={runSimulation}
                disabled={running}
              >
                <Play size={20} fill="currentColor" />

                <span>
                  {running ? "Running..." : "Run Simulation"}
                </span>
              </button>
            </div>

            {/* STATUS */}
            <div
              className={`simulation-status ${
                completed ? "status-success" : "status-running"
              }`}
            >
              {completed ? (
                <>
                  <CheckCircle2 size={19} />

                  <span>
                    Simulation completed using the selected
                    parameters.
                  </span>
                </>
              ) : (
                <>
                  <Sparkles size={19} />

                  <span>
                    Running simulation with the selected
                    parameters...
                  </span>
                </>
              )}
            </div>
          </section>

          {/* =================================================
              SCENARIOS
          ================================================== */}
          <section className="scenario-section">
            <div className="scenario-heading-row">
              <div className="scenario-title">
                <div className="scenario-title-icon">
                  <BarChart3 size={25} />
                </div>

                <div>
                  <h2>Scenario Comparison</h2>

                  <p>
                    See how timing and market conditions impact
                    your voyage cost and risk
                  </p>
                </div>
              </div>

              <div className="scenario-info">
                <Info size={20} />

                <p>
                  The cheapest freight rate does not always mean
                  the lowest total voyage cost. Consider total
                  cost, risk, and expected delays before making a
                  decision.
                </p>
              </div>
            </div>

            <div className="scenario-grid">
              {(simulationResult
                ? [
                    {
                      id: "base",
                      title: "Base Scenario",
                      date: getVoyageInput()?.arrivalDate || charteringDate,
                      rate: "Unavailable",
                      cost:
                        simulationResult.base_scenario?.total_landed_cost != null
                          ? `$ ${Number(
                              simulationResult.base_scenario.total_landed_cost
                            ).toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}`
                          : "Unavailable",
                      risk:
                        simulationResult.base_scenario?.risk?.risk_level || "Unavailable",
                      delay: "Unavailable",
                      type:
                        String(
                          simulationResult.base_scenario?.risk?.risk_level || ""
                        ).toLowerCase() === "high"
                          ? "high"
                          : String(
                              simulationResult.base_scenario?.risk?.risk_level || ""
                            ).toLowerCase() === "medium"
                          ? "moderate"
                          : "low",
                      recommended:
                        simulationResult.base_scenario?.recommendation?.strategy === "BOOK_NOW",
                      message:
                        simulationResult.base_scenario?.recommendation?.strategy ||
                        "Base scenario result unavailable.",
                    },
                    {
                      id: "modified",
                      title:
                        Number(waitingPeriod) === 0
                          ? "Charter Now"
                          : `Wait ${waitingPeriod} Days`,
                      date: addDays(
                        getVoyageInput()?.arrivalDate || charteringDate,
                        waitingPeriod
                      ),
                      rate: "Unavailable",
                      cost:
                        simulationResult.modified_scenario
                          ?.total_landed_cost != null
                          ? `$ ${Number(
                              simulationResult.modified_scenario
                                .total_landed_cost
                            ).toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}`
                          : "Unavailable",
                      risk:
                        simulationResult.modified_scenario?.risk?.risk_level ||
                        "Unavailable",
                      delay: "Unavailable",
                      type:
                        String(
                          simulationResult.modified_scenario?.risk?.risk_level || ""
                        ).toLowerCase() === "high"
                          ? "high"
                          : String(
                              simulationResult.modified_scenario?.risk?.risk_level || ""
                            ).toLowerCase() === "medium"
                          ? "moderate"
                          : "low",
                      recommended:
                        simulationResult.modified_scenario?.recommendation?.strategy ===
                        "BOOK_NOW",
                      message:
                        simulationResult.modified_scenario?.recommendation?.strategy ||
                        "Modified scenario result unavailable.",
                    },
                  ]
                : scenarios
              ).map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                />
              ))}
            </div>
          </section>

          {/* =================================================
              INSIGHT
          ================================================== */}
          <section className="decision-insight">
            <div className="decision-insight-icon">
              <Sparkles size={22} />
            </div>

            <div>
              <h3>FreightWise Recommendation</h3>

              <p>
                {simulationError
                  ? simulationError
                  : simulationResult
                  ? `Base strategy: ${
                      simulationResult.base_scenario?.recommendation?.strategy ||
                      "Unavailable"
                    }. Modified strategy: ${
                      simulationResult.modified_scenario?.recommendation?.strategy ||
                      "Unavailable"
                    }. Recommendation changed: ${
                      simulationResult.recommendation_changed ? "Yes" : "No"
                    }.`
                  : "Run the simulation to compare the selected scenario against the base voyage."}
              </p>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

/* =========================================================
   SCENARIO CARD
========================================================= */

function ScenarioCard({ scenario }) {
  return (
    <article
      className={`scenario-card scenario-${scenario.type} ${
        scenario.recommended ? "recommended-card" : ""
      }`}
    >
      {scenario.recommended && (
        <div className="recommended-badge">
          <ShieldCheck size={17} />

          <span>Recommended</span>
        </div>
      )}

      <div className="scenario-card-header">
        <div className="scenario-heading">
          <div className="scenario-main-icon">
            {scenario.id === "7" ? (
              <Clock3 size={25} />
            ) : (
              <CalendarDays size={25} />
            )}
          </div>

          <div>
            <h3>{scenario.title}</h3>

            <p>{scenario.date}</p>
          </div>
        </div>

        <img
          src={simulImage}
          alt="Cargo vessel"
          className="scenario-ship-image"
        />
      </div>

      <div className="card-divider" />

      <div className="scenario-metrics">
        {/* RATE */}
        <div className="metric">
          <div className="metric-icon dollar-icon">$</div>

          <div>
            <span>Freight Rate</span>

            <strong>{scenario.rate}</strong>
          </div>
        </div>

        {/* COST */}
        <div className="metric">
          <div className="metric-icon">
            <BarChart3 size={19} />
          </div>

          <div>
            <span>Total Cost</span>

            <strong>{scenario.cost}</strong>
          </div>
        </div>

        {/* RISK */}
        <div className="metric">
          <div className="metric-icon">
            <ShieldCheck size={19} />
          </div>

          <div>
            <span>Overall Risk</span>

            <strong
              className={`risk-pill risk-${scenario.type}`}
            >
              {scenario.risk}
            </strong>
          </div>
        </div>

        {/* DELAY */}
        <div className="metric">
          <div className="metric-icon">
            <Clock3 size={19} />
          </div>

          <div>
            <span>Expected Delay</span>

            <strong>{scenario.delay}</strong>
          </div>
        </div>
      </div>

      <div className="scenario-message">
        <ShieldCheck size={20} />

        <p>{scenario.message}</p>
      </div>
    </article>
  );
}

export default Simulation;