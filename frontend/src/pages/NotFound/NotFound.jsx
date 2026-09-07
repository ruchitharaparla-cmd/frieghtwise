import React from "react";
import {
  Search,
  Bell,
  ChevronDown,
  Home,
  PlusCircle,
  Ship,
  MapPin,
  ArrowRight,
  ArrowLeft,
  LayoutDashboard,
  BarChart3,
  RotateCcw,
  Settings as SettingsIcon,
} from "lucide-react";

import "./NotFound.css";


const navigationItems = [
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
    icon: MapPin,
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


const quickLinks = [
  {
    title: "Go to Dashboard",
    subtitle: "View your overview",
    path: "/",
    icon: Home,
  },
  {
    title: "Plan a New Voyage",
    subtitle: "Explore new opportunities",
    path: "/new-voyage",
    icon: PlusCircle,
  },
  {
    title: "Browse Vessels",
    subtitle: "Find the right vessel",
    path: "/vessels",
    icon: Ship,
  },
  {
    title: "View Ports",
    subtitle: "Explore global ports",
    path: "/ports",
    icon: MapPin,
  },
];


const NotFound = () => {
  const handleGoBack = () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = "/";
    }
  };

  return (
    <div className="not-found-page">

      {/* =====================================================
          SIDEBAR
      ===================================================== */}

      <aside className="not-found-sidebar">

        <div className="not-found-brand">

          <div className="not-found-brand-mark">
            <Ship
              size={36}
              strokeWidth={1.5}
            />
          </div>

          <h1>FREIGHTWISE</h1>

          <p>
            Navigate Smarter.
            <br />
            Charter Better.
          </p>

        </div>


        <nav className="not-found-navigation">

          {navigationItems.map((item) => {
            const Icon = item.icon;

            return (
              <a
                key={item.label}
                href={item.path}
                className="not-found-nav-item"
              >
                <Icon
                  size={20}
                  strokeWidth={1.8}
                />

                <span>
                  {item.label}
                </span>
              </a>
            );
          })}

        </nav>


        {/* Sidebar bottom status */}

        <div className="not-found-sidebar-bottom">

          <div className="not-found-ai-card">

            <div className="not-found-ai-title">

              <span className="not-found-online-dot"></span>

              <span>
                AI Engine Online
              </span>

            </div>

            <div className="not-found-ai-update">
              Data updated
              <br />
              2 min ago
            </div>

          </div>


          <div className="not-found-wave"></div>


          <div className="not-found-sidebar-quote">
            “Right Data.
            <br />
            Smarter Decisions.
            <br />
            Greener Seas.”
          </div>

        </div>

      </aside>



      {/* =====================================================
          MAIN CONTENT
      ===================================================== */}

      <main className="not-found-main">


        {/* ===================================================
            TOP BAR
        =================================================== */}

        <header className="not-found-topbar">

          <div className="not-found-search">

            <Search size={20} />

            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />

          </div>


          <div className="not-found-topbar-actions">

            <button
              type="button"
              className="not-found-notification"
              aria-label="Notifications"
            >

              <Bell size={22} />

              <span>3</span>

            </button>


            <div className="not-found-topbar-divider"></div>


            <button
              type="button"
              className="not-found-user"
            >

              <div className="not-found-user-avatar">
                U
              </div>

              <span>
                User
              </span>

              <ChevronDown size={17} />

            </button>

          </div>

        </header>



        {/* ===================================================
            PAGE CONTENT
        =================================================== */}

        <section className="not-found-content">


          {/* =================================================
              FULL WIDTH MARITIME HERO
          ================================================= */}

          <div className="not-found-hero">


            {/* Full background ship image */}

            <div className="not-found-ship-background"></div>


            {/* Soft overlay */}

            <div className="not-found-hero-overlay"></div>


            {/* Decorative 404 */}

            <div className="not-found-background-number">
              404
            </div>


            {/* Decorative clouds */}

            <div className="not-found-cloud cloud-one"></div>

            <div className="not-found-cloud cloud-two"></div>


            {/* Birds */}

            <div className="not-found-bird bird-one">
              ︿
            </div>

            <div className="not-found-bird bird-two">
              ︿
            </div>


            {/* Lighthouse */}

            <div className="not-found-lighthouse">
              <span></span>
            </div>


            {/* Water reflections */}

            <div className="not-found-water water-one"></div>

            <div className="not-found-water water-two"></div>

            <div className="not-found-water water-three"></div>

          </div>



          {/* =================================================
              ERROR MESSAGE
          ================================================= */}

          <div className="not-found-message">

            <h2>
              Page Not Found
            </h2>

            <p>
              The page you're looking for doesn't exist or has been moved.
            </p>

            <span>
              Let's get you back on course.
            </span>

          </div>



          {/* =================================================
              QUICK ACTION CARDS
          ================================================= */}

          <div className="not-found-quick-links">

            {quickLinks.map((item) => {
              const Icon = item.icon;

              return (
                <a
                  key={item.title}
                  href={item.path}
                  className="not-found-quick-card"
                >

                  <div className="quick-card-icon">
                    <Icon
                      size={28}
                      strokeWidth={1.7}
                    />
                  </div>


                  <div className="quick-card-content">

                    <strong>
                      {item.title}
                    </strong>

                    <span>
                      {item.subtitle}
                    </span>

                    <div className="quick-card-arrow">
                      <ArrowRight size={20} />
                    </div>

                  </div>

                </a>
              );
            })}

          </div>



          {/* =================================================
              OR
          ================================================= */}

          <div className="not-found-or">

            <span></span>

            <strong>
              OR
            </strong>

            <span></span>

          </div>



          {/* =================================================
              GO BACK
          ================================================= */}

          <button
            type="button"
            className="not-found-go-back"
            onClick={handleGoBack}
          >

            <ArrowLeft size={20} />

            <span>
              Go Back
            </span>

          </button>


        </section>



        {/* ===================================================
            FOOTER
        =================================================== */}

        <footer className="not-found-footer">

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
};


export default NotFound;