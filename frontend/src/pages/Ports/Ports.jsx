import React, { useState } from "react";
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
  ArrowUp,
  ArrowDown,
  Clock,
} from "lucide-react";

import "./Ports.css";


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

const portsData = [
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

  const [search, setSearch] = useState("");

  const [statusFilter, setStatusFilter] =
    useState("All");


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
            <Ship size={35} strokeWidth={1.6} />
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
              <a
                key={item.label}
                href={item.path}
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

              </a>
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

            <a
              href="/notifications"
              className="ports-notification"
            >

              <Bell size={20} />

              <span>
                3
              </span>

            </a>


            <div className="ports-divider"></div>


            <a
              href="/profile"
              className="ports-user"
            >

              <div className="ports-avatar">
                U
              </div>

              <span>
                User
              </span>

              <ChevronDown size={15} />

            </a>

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


          {/* SUMMARY */}

          <div className="ports-summary">

            <div className="ports-summary-card">

              <div className="ports-summary-icon">
                <Anchor size={23} />
              </div>

              <div>
                <span>
                  Total Ports
                </span>

                <strong>
                  {portsData.length}
                </strong>
              </div>

            </div>


            <div className="ports-summary-card">

              <div className="ports-summary-icon low">
                <Clock size={23} />
              </div>

              <div>
                <span>
                  Low Congestion
                </span>

                <strong>
                  {
                    portsData.filter(
                      (port) => port.status === "Low"
                    ).length
                  }
                </strong>
              </div>

            </div>


            <div className="ports-summary-card">

              <div className="ports-summary-icon moderate">
                <Clock size={23} />
              </div>

              <div>
                <span>
                  Moderate
                </span>

                <strong>
                  {
                    portsData.filter(
                      (port) => port.status === "Moderate"
                    ).length
                  }
                </strong>
              </div>

            </div>


            <div className="ports-summary-card">

              <div className="ports-summary-icon high">
                <Clock size={23} />
              </div>

              <div>
                <span>
                  High Congestion
                </span>

                <strong>
                  {
                    portsData.filter(
                      (port) => port.status === "High"
                    ).length
                  }
                </strong>
              </div>

            </div>

          </div>


          {/* FILTER */}

          <div className="ports-filter-bar">

            <div>

              <h3>
                East Coast Port Status
              </h3>

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
                Congestion
              </span>

              <span>
                Trend
              </span>

            </div>


            {filteredPorts.map((port) => (

              <div
                className="ports-table-row"
                key={port.name}
              >

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


                <div
                  className={
                    `ports-status ${port.statusClass}`
                  }
                >

                  <i></i>

                  {port.status}

                </div>


                <div className="ports-waiting">

                  <Clock size={15} />

                  {port.waiting}

                </div>


                <div className="ports-congestion">

                  <div className="congestion-bar">

                    <span
                      style={{
                        width: port.congestion
                      }}
                    ></span>

                  </div>

                  <small>
                    {port.congestion}
                  </small>

                </div>


                <div
                  className={
                    `ports-trend ${port.trend}`
                  }
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


        </section>


        {/* FOOTER */}

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