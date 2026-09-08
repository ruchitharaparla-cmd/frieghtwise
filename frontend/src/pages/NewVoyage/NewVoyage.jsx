import React, { useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  Ship,
  LayoutDashboard,
  PlusCircle,
  BarChart3,
  Anchor,
  RotateCcw,
  Settings as SettingsIcon,
  Clock,
} from "lucide-react";

import "./NewVoyage.css";


/* =========================================================
   SIDEBAR
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
   VOYAGE DATA
========================================================= */

const voyageData = [
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


function Voyages() {

  const [search, setSearch] = useState("");

  const [statusFilter, setStatusFilter] =
    useState("All");


  const filteredVoyages = voyageData.filter((voyage) => {

    const searchValue =
      search.toLowerCase();


    const matchesSearch =
      voyage.id
        .toLowerCase()
        .includes(searchValue) ||
      voyage.cargo
        .toLowerCase()
        .includes(searchValue) ||
      voyage.route
        .toLowerCase()
        .includes(searchValue);


    const matchesStatus =
      statusFilter === "All" ||
      voyage.status === statusFilter;


    return matchesSearch && matchesStatus;
  });


  return (
    <div className="voyages-page">


      {/* =================================================
          SIDEBAR
      ================================================= */}

      <aside className="voyages-sidebar">

        <div className="voyages-brand">

          <div className="voyages-brand-logo">
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


        <nav className="voyages-navigation">

          {mainNavigation.map((item) => {

            const Icon = item.icon;

            return (
              <a
                key={item.label}
                href={item.path}
                className="voyages-nav-item"
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


        <div className="voyages-sidebar-bottom">

          <div className="voyages-ai-status">

            <div className="voyages-ai-header">

              <span className="voyages-online-dot"></span>

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


          <div className="voyages-sidebar-wave"></div>


          <div className="voyages-sidebar-quote">
            "Smarter Oceans
            <br />
            for a Stronger India."
          </div>

        </div>

      </aside>


      {/* =================================================
          MAIN
      ================================================= */}

      <main className="voyages-main">


        {/* TOPBAR */}

        <header className="voyages-topbar">

          <div className="voyages-search">

            <Search size={18} />

            <input
              type="text"
              placeholder="Search voyages, cargo, routes..."
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
            />

          </div>


          <div className="voyages-topbar-right">

            <a
              href="/notifications"
              className="voyages-notification"
            >

              <Bell size={20} />

              <span>
                3
              </span>

            </a>


            <div className="voyages-divider"></div>


            <a
              href="/profile"
              className="voyages-user"
            >

              <div className="voyages-avatar">
                U
              </div>

              <span>
                User
              </span>

              <ChevronDown size={15} />

            </a>

          </div>

        </header>


        {/* PAGE HEADER */}

        <section className="voyages-header">

          <div>

            <div className="voyages-kicker">
              VOYAGE MANAGEMENT
            </div>

            <h2>
              All Voyages
            </h2>

            <p>
              Review your voyage activity, cargo movements,
              routes and chartering costs
            </p>

          </div>


          <div className="voyages-header-icon">

            <Ship
              size={84}
              strokeWidth={1.2}
            />

          </div>

        </section>


        {/* CONTENT */}

        <section className="voyages-content">


          {/* SUMMARY */}

          <div className="voyages-summary">

            <div className="voyages-summary-card">

              <div className="voyages-summary-icon">
                <Ship size={23} />
              </div>

              <div>

                <span>
                  Total Voyages
                </span>

                <strong>
                  {voyageData.length}
                </strong>

              </div>

            </div>


            <div className="voyages-summary-card">

              <div className="voyages-summary-icon transit">
                <Clock size={23} />
              </div>

              <div>

                <span>
                  In Transit
                </span>

                <strong>
                  {
                    voyageData.filter(
                      (voyage) =>
                        voyage.status === "In Transit"
                    ).length
                  }
                </strong>

              </div>

            </div>


            <div className="voyages-summary-card">

              <div className="voyages-summary-icon loading">
                <Ship size={23} />
              </div>

              <div>

                <span>
                  Loading
                </span>

                <strong>
                  {
                    voyageData.filter(
                      (voyage) =>
                        voyage.status === "Loading"
                    ).length
                  }
                </strong>

              </div>

            </div>


            <div className="voyages-summary-card">

              <div className="voyages-summary-icon completed">
                <Ship size={23} />
              </div>

              <div>

                <span>
                  Completed
                </span>

                <strong>
                  {
                    voyageData.filter(
                      (voyage) =>
                        voyage.status === "Completed"
                    ).length
                  }
                </strong>

              </div>

            </div>

          </div>


          {/* TABLE HEADER */}

          <div className="voyages-table-card">

            <div className="voyages-table-toolbar">

              <div>

                <h3>
                  Voyage History
                </h3>

                <p>
                  All recorded FreightWise voyages
                </p>

              </div>


              <div className="voyages-toolbar-controls">

                <select
                  value={statusFilter}
                  onChange={(event) =>
                    setStatusFilter(event.target.value)
                  }
                >

                  <option value="All">
                    All Status
                  </option>

                  <option value="Completed">
                    Completed
                  </option>

                  <option value="In Transit">
                    In Transit
                  </option>

                  <option value="Loading">
                    Loading
                  </option>

                </select>

              </div>

            </div>


            {/* TABLE */}

            <div className="voyages-table">

              <div className="voyages-table-heading">

                <span>
                  Voyage
                </span>

                <span>
                  Cargo
                </span>

                <span>
                  Route
                </span>

                <span>
                  Status
                </span>

                <span>
                  Cost
                </span>

              </div>


              {filteredVoyages.map((voyage) => (

                <div
                  className="voyages-table-row"
                  key={voyage.id}
                >

                  <div className="voyage-id-cell">

                    <div className="voyage-ship-icon">
                      <Ship size={18} />
                    </div>

                    <div>

                      <strong>
                        {voyage.id}
                      </strong>

                      <span>
                        FreightWise Voyage
                      </span>

                    </div>

                  </div>


                  <div className="voyage-cargo">
                    {voyage.cargo}
                  </div>


                  <div className="voyage-route">
                    {voyage.route}
                  </div>


                  <div
                    className={
                      `voyage-status ${voyage.statusClass}`
                    }
                  >

                    <i></i>

                    {voyage.status}

                  </div>


                  <strong className="voyage-cost">
                    {voyage.cost}
                  </strong>

                </div>

              ))}


              {filteredVoyages.length === 0 && (

                <div className="voyages-empty">

                  <Ship size={42} />

                  <h3>
                    No voyages found
                  </h3>

                  <p>
                    Try a different search or status filter.
                  </p>

                </div>

              )}

            </div>

          </div>


        </section>


        {/* FOOTER */}

        <footer className="voyages-footer">

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


export default Voyages;