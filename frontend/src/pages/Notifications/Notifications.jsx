import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  Bell,
  ChevronDown,
  TrendingUp,
  CalendarDays,
  AlertTriangle,
  CloudRain,
  Mail,
  Activity,
  LayoutDashboard,
  PlusCircle,
  BarChart3,
  Ship,
  Anchor,
  RotateCcw,
  Settings as SettingsIcon,
  CheckCircle2,
  Clock3,
  X,
} from "lucide-react";

import "./Notifications.css";


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


const notificationData = [
  {
    id: 1,
    icon: TrendingUp,
    title: "Freight Rate Alert",
    description:
      "Freight rates for your selected route are expected to decline over the next 10 days.",
    time: "10 minutes ago",
    type: "Market",
    unread: true,
  },
  {
    id: 2,
    icon: CalendarDays,
    title: "Favorable Chartering Window",
    description:
      "A favorable chartering window has been detected for your upcoming voyage.",
    time: "35 minutes ago",
    type: "Voyage",
    unread: true,
  },
  {
    id: 3,
    icon: AlertTriangle,
    title: "Port Congestion Alert",
    description:
      "Port congestion may affect waiting times at Paradip. Consider monitoring alternate arrival windows.",
    time: "1 hour ago",
    type: "Port",
    unread: true,
  },
  {
    id: 4,
    icon: CloudRain,
    title: "Weather & Maritime Risk",
    description:
      "Weather conditions in the Bay of Bengal are being monitored for potential voyage impact.",
    time: "2 hours ago",
    type: "Risk",
    unread: false,
  },
  {
    id: 5,
    icon: Mail,
    title: "Market Digest",
    description:
      "Your latest freight market summary is available with updated regional market movements.",
    time: "Yesterday",
    type: "Market",
    unread: false,
  },
  {
    id: 6,
    icon: Activity,
    title: "Model & System Update",
    description:
      "FreightWise forecasting systems have been updated with the latest intelligence models.",
    time: "Yesterday",
    type: "System",
    unread: false,
  },
];


function Notifications() {

  const [notifications, setNotifications] =
    useState(notificationData);


  const [filter, setFilter] =
    useState("All");


  const markAllAsRead = () => {
    setNotifications((previous) =>
      previous.map((item) => ({
        ...item,
        unread: false,
      }))
    );
  };


  const markAsRead = (id) => {
    setNotifications((previous) =>
      previous.map((item) =>
        item.id === id
          ? { ...item, unread: false }
          : item
      )
    );
  };


  const filteredNotifications =
    filter === "Unread"
      ? notifications.filter((item) => item.unread)
      : notifications;


  const unreadCount =
    notifications.filter((item) => item.unread).length;


  return (
    <div className="notifications-page">


      {/* =========================
          SIDEBAR
      ========================= */}

      <aside className="notifications-sidebar">

        <div className="notifications-brand">

          <div className="notifications-brand-logo">
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


        <nav className="notifications-main-navigation">

          {mainNavigation.map((item) => {

            const Icon = item.icon;

            return (
              <button
                key={item.label}
                type="button"
                onClick={() => navigate(item.path)}
                className="notifications-main-nav-item"
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


        <div className="notifications-sidebar-bottom">

          <div className="notifications-ai-status">

            <div className="notifications-ai-header">

              <span className="notifications-online-dot"></span>

              <span>
                AI Engine Online
              </span>

            </div>

            <p>
              Intelligence systems operational
            </p>

          </div>


          <div className="notifications-sidebar-wave"></div>


          <div className="notifications-sidebar-quote">
            “Right Data.
            <br />
            Smarter Decisions.
            <br />
            Greener Seas.”
          </div>

        </div>

      </aside>


      {/* =========================
          MAIN
      ========================= */}

      <main className="notifications-main">


        {/* TOPBAR */}

        <header className="notifications-topbar">

          <div className="notifications-search">

            <Search size={19} />

            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />

          </div>


          <div className="notifications-topbar-actions">

            <div className="notifications-bell">

              <Bell size={21} />

              {unreadCount > 0 && (
                <span>
                  {unreadCount}
                </span>
              )}

            </div>


            <div className="notifications-topbar-divider"></div>


            <button
              type="button"
              onClick={() => navigate("/profile")}
              className="notifications-user-menu"
            >

              <div className="notifications-user-avatar">
                U
              </div>

              <span>
                User
              </span>

              <ChevronDown size={16} />

            </button>

          </div>

        </header>


        {/* HEADER */}

        <section className="notifications-header">

          <div>

            <div className="notifications-kicker">
              ALERT CENTER
            </div>

            <h2>
              Notifications
            </h2>

            <p>
              Stay informed about freight markets, voyages,
              ports and maritime risks
            </p>

          </div>


          <div className="notifications-header-icon">
            <Bell size={75} strokeWidth={1.2} />
          </div>

        </section>


        {/* CONTENT */}

        <section className="notifications-content">


          {/* SUMMARY */}

          <div className="notifications-summary">

            <div className="notifications-summary-card">

              <div className="notifications-summary-icon">
                <Bell size={22} />
              </div>

              <div>

                <span>
                  Total Notifications
                </span>

                <strong>
                  {notifications.length}
                </strong>

              </div>

            </div>


            <div className="notifications-summary-card">

              <div className="notifications-summary-icon unread">
                <Activity size={22} />
              </div>

              <div>

                <span>
                  Unread
                </span>

                <strong>
                  {unreadCount}
                </strong>

              </div>

            </div>


            <button
              type="button"
              className="mark-all-button"
              onClick={markAllAsRead}
            >
              <CheckCircle2 size={17} />
              Mark all as read
            </button>

          </div>


          {/* FILTERS */}

          <div className="notifications-toolbar">

            <div className="notification-filter">

              <button
                type="button"
                className={
                  filter === "All"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setFilter("All")
                }
              >
                All
              </button>


              <button
                type="button"
                className={
                  filter === "Unread"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setFilter("Unread")
                }
              >
                Unread
              </button>

            </div>

          </div>


          {/* NOTIFICATION LIST */}

          <div className="notification-list">

            {filteredNotifications.length === 0 ? (

              <div className="notifications-empty">

                <CheckCircle2 size={45} />

                <h3>
                  You're all caught up
                </h3>

                <p>
                  There are no unread notifications.
                </p>

              </div>

            ) : (

              filteredNotifications.map((item) => {

                const Icon = item.icon;

                return (
                  <div
                    key={item.id}
                    className={
                      item.unread
                        ? "notification-item unread"
                        : "notification-item"
                    }
                  >

                    <div className="notification-item-icon">
                      <Icon size={22} />
                    </div>


                    <div className="notification-item-content">

                      <div className="notification-item-title">

                        <h3>
                          {item.title}
                        </h3>

                        {item.unread && (
                          <span className="unread-dot"></span>
                        )}

                      </div>


                      <p>
                        {item.description}
                      </p>


                      <div className="notification-item-meta">

                        <span>
                          <Clock3 size={13} />
                          {item.time}
                        </span>

                        <span className="notification-type">
                          {item.type}
                        </span>

                      </div>

                    </div>


                    {item.unread && (
                      <button
                        type="button"
                        className="notification-read-button"
                        onClick={() =>
                          markAsRead(item.id)
                        }
                        aria-label="Mark notification as read"
                      >
                        <CheckCircle2 size={18} />
                      </button>
                    )}

                  </div>
                );

              })

            )}

          </div>

        </section>


        {/* FOOTER */}

        <footer className="notifications-footer">

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


export default Notifications;