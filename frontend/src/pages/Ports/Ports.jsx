import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Search,
  Bell,
  ChevronDown,
  Anchor,
  LayoutDashboard,
  PlusCircle,
  BarChart3,
  Ship,
  RotateCcw,
  Settings as SettingsIcon,
  Clock,
} from "lucide-react";

import PortCard from "../../components/ports/PortCard";
import PortTable from "../../components/ports/PortTable";

import "./Ports.css";
import { getPorts } from "../../services/api";


/* =========================================================
   SIDEBAR NAVIGATION
========================================================= */

const mainNavigation = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
  },

  {
    label: "New Voyage",
    path: "/new-voyage",
    icon: PlusCircle,
  },

  {
    label: "Analysis",
    path: "/analysis",
    icon: BarChart3,
  },

  {
    label: "Vessels",
    path: "/vessels",
    icon: Ship,
  },

  {
    label: "Ports",
    path: "/ports",
    icon: Anchor,
  },

  {
    label: "Simulation",
    path: "/simulation",
    icon: RotateCcw,
  },

  {
    label: "Settings",
    path: "/settings",
    icon: SettingsIcon,
  },
];


/* =========================================================
   PORT DATA
========================================================= */

const demoPortsData = [
  {
    name: "Kolkata",
    location: "West Bengal",
    status: "Low",
    statusClass: "low",
    waiting: "12 h",
    trend: "up",
    congestion: "18%",
  },

  {
    name: "Paradip",
    location: "Odisha",
    status: "Moderate",
    statusClass: "moderate",
    waiting: "28 h",
    trend: "down",
    congestion: "42%",
  },

  {
    name: "Visakhapatnam",
    location: "Andhra Pradesh",
    status: "Low",
    statusClass: "low",
    waiting: "16 h",
    trend: "up",
    congestion: "22%",
  },

  {
    name: "Kakinada",
    location: "Andhra Pradesh",
    status: "Moderate",
    statusClass: "moderate",
    waiting: "24 h",
    trend: "down",
    congestion: "36%",
  },

  {
    name: "Chennai",
    location: "Tamil Nadu",
    status: "High",
    statusClass: "high",
    waiting: "46 h",
    trend: "down",
    congestion: "68%",
  },

  {
    name: "Krishnapatnam",
    location: "Andhra Pradesh",
    status: "Low",
    statusClass: "low",
    waiting: "18 h",
    trend: "up",
    congestion: "25%",
  },
];


function Ports() {
  const navigate = useNavigate();

  const [portsData, setPortsData] = useState([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");

  const [statusFilter, setStatusFilter] =
    useState("All");


  /* =========================================================
     FILTER PORTS
  ========================================================= */

  useEffect(() => {
    async function loadPorts() {
      try {
        const data = await getPorts();

        const apiPorts = Array.isArray(data?.ports)
          ? data.ports
          : Array.isArray(data)
          ? data
          : [];

        const normalized = apiPorts.map((port) => {
              const utilization = port.utilization_percent;

              let status = "Unavailable";
              let statusClass = "moderate";

              if (typeof utilization === "number") {
                if (utilization < 50) {
                  status = "Low";
                  statusClass = "low";
                } else if (utilization < 80) {
                  status = "Moderate";
                  statusClass = "moderate";
                } else {
                  status = "High";
                  statusClass = "high";
                }
              }

              return {
                id: port.id,
                name: port.name || "Name unavailable",
                location: port.state || "Location unavailable",
                status,
                statusClass,
                waiting:
                  typeof port.average_waiting_hours === "number"
                    ? `${port.average_waiting_hours} h`
                    : "Unavailable",
                trend: "unavailable",
                congestion:
                  typeof utilization === "number"
                    ? `${utilization}%`
                    : "Unavailable",
              };
            });

        setPortsData(normalized);
      } catch (error) {
        console.error("Failed to load ports:", error);
        setPortsData([]);
      } finally {
        setLoading(false);
      }
    }

    loadPorts();
  }, []);

  const filteredPorts = portsData.filter((port) => {
    const matchesSearch =
      port.name
        .toLowerCase()
        .includes(search.toLowerCase()) ||
      port.location
        .toLowerCase()
        .includes(search.toLowerCase());

    const matchesStatus =
      statusFilter === "All" ||
      port.status === statusFilter;

    return matchesSearch && matchesStatus;
  });


  return (
    <div className="ports-page">


      {/* =================================================
          SIDEBAR
      ================================================= */}

      <aside className="ports-sidebar">

        <div className="ports-brand">

          <div className="ports-brand-logo">
            <Ship
              size={35}
              strokeWidth={1.6}
            />
          </div>

          <h1>
            FREIGHTWISE
          </h1>

          <p>
            Navigate Smarter.
            <br />
            Charter Better.
          </p>

        </div>


        <nav className="ports-navigation">

          {mainNavigation.map((item) => {

            const Icon = item.icon;

            return (
              <button
                type="button"
                key={item.label}
                onClick={() => navigate(item.path)}
                className={
                  item.label === "Ports"
                    ? "ports-nav-item active"
                    : "ports-nav-item"
                }
              >

                <Icon
                  size={19}
                  strokeWidth={1.8}
                />

                <span>
                  {item.label}
                </span>

              </button>
            );

          })}

        </nav>


        <div className="ports-sidebar-bottom">

          <div className="ports-ai-status">

            <div className="ports-ai-header">

              <span className="ports-online-dot"></span>

              <span>
                AI Engine Online
              </span>

            </div>

            <p>
              Data updated
            </p>

            <strong>
              2 min ago
            </strong>

          </div>


          <div className="ports-sidebar-wave"></div>


          <div className="ports-sidebar-quote">
            "Smarter Oceans
            <br />
            for a Stronger India."
          </div>

        </div>

      </aside>


      {/* =================================================
          MAIN
      ================================================= */}

      <main className="ports-main">


        {/* =================================================
            TOPBAR
        ================================================= */}

        <header className="ports-topbar">

          <div className="ports-search">

            <Search size={18} />

            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
            />

          </div>


          <div className="ports-topbar-right">

            <button
              type="button"
              className="ports-notification"
              onClick={() => navigate("/notifications")}
            >

              <Bell size={20} />

              <span>
                3
              </span>

            </button>


            <div className="ports-divider"></div>


            <button
              type="button"
              className="ports-user"
              onClick={() => navigate("/profile")}
            >

              <div className="ports-avatar">
                U
              </div>

              <span>
                User
              </span>

              <ChevronDown size={15} />

            </button>

          </div>

        </header>


        {/* =================================================
            PAGE HEADER
        ================================================= */}

        <section className="ports-header">

          <div>

            <div className="ports-kicker">
              PORT INTELLIGENCE
            </div>

            <h2>
              All Ports
            </h2>

            <p>
              Monitor port congestion, waiting times and
              operational conditions across India's East Coast
            </p>

          </div>


          <div className="ports-header-icon">

            <Anchor
              size={82}
              strokeWidth={1.2}
            />

          </div>

        </section>


        {/* =================================================
            CONTENT
        ================================================= */}

        <section className="ports-content">
          {loading && (
            <div className="ports-loading">
              Loading ports from backend...
            </div>
          )}


          {/* =================================================
              SUMMARY CARDS
          ================================================= */}

          <div className="ports-summary">

            <PortCard
              icon={Anchor}
              title="Total Ports"
              value={portsData.length}
            />


            <PortCard
              icon={Clock}
              title="Low Congestion"
              value={
                portsData.filter(
                  (port) =>
                    port.status === "Low"
                ).length
              }
              type="low"
            />


            <PortCard
              icon={Clock}
              title="Moderate"
              value={
                portsData.filter(
                  (port) =>
                    port.status === "Moderate"
                ).length
              }
              type="moderate"
            />


            <PortCard
              icon={Clock}
              title="High Congestion"
              value={
                portsData.filter(
                  (port) =>
                    port.status === "High"
                ).length
              }
              type="high"
            />

          </div>


          {/* =================================================
              PORT TABLE + FILTER
          ================================================= */}

          <PortTable
            filteredPorts={filteredPorts}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
          />

        </section>


        {/* =================================================
            FOOTER
        ================================================= */}

        <footer className="ports-footer">

          <span>
            © 2026 FreightWise. All rights reserved.
          </span>

          <div>

            <a href="#help">
              Help
            </a>

            <a href="#privacy">
              Privacy
            </a>

            <a href="#terms">
              Terms
            </a>

            <a href="#contact">
              Contact
            </a>

          </div>

        </footer>

      </main>

    </div>
  );
}


export default Ports;