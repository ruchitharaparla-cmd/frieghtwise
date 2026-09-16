import React from "react";
import {
  Search,
  Bell,
  ChevronDown,
} from "lucide-react";

export default function Header() {
  return (
    <header className="fw-header">
      <div className="fw-header-left">
        <span className="fw-header-section">
          FREIGHT OPERATIONS
        </span>

        <span className="fw-header-slash">/</span>

        <span className="fw-header-workspace">
          Live workspace
        </span>
      </div>

      <div className="fw-header-right">
        <button
          type="button"
          className="fw-header-icon-button"
          aria-label="Search"
        >
          <Search size={22} strokeWidth={2} />
        </button>

        <button
          type="button"
          className="fw-header-icon-button fw-notification-button"
          aria-label="Notifications"
        >
          <Bell size={22} strokeWidth={2} />
          <span className="fw-notification-dot" />
        </button>

        <div className="fw-header-divider" />

        <button
          type="button"
          className="fw-profile-button"
          aria-label="Open profile menu"
        >
          <span className="fw-profile-avatar">R</span>

          <span className="fw-profile-content">
            <strong>Ruchitha</strong>
            <small>Voyage Planner</small>
          </span>

          <ChevronDown
            size={18}
            strokeWidth={2}
          />
        </button>
      </div>
    </header>
  );
}