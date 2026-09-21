import React from "react";
import { useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  PlusCircle,
  BarChart3,
  Ship,
  Anchor,
  FlaskConical,
  Settings,
  LogOut,
} from "lucide-react";

const items = [
  ["dashboard", "Dashboard", LayoutDashboard],
  ["new-voyage", "New Voyage", PlusCircle],
  ["analysis", "Analysis", BarChart3],
  ["simulation", "Simulation", FlaskConical],
  ["vessels", "Vessels", Ship],
  ["ports", "Ports", Anchor],
];

export default function Sidebar({ page, setPage }) {
  const navigate = useNavigate();

  return (
    <aside className="fw-sidebar">
      <div className="fw-brand">
        <img src="/assets/freightwise-logo.png" alt="FreightWise logo" />
        <div>
          <strong>FreightWise</strong>
          <small>Maritime Intelligence</small>
        </div>
      </div>

      <nav className="fw-sidebar-nav">
        {items.map(([id, label, Icon]) => (
          <button
            key={id}
            type="button"
            className={page === id ? "active" : ""}
            onClick={() => setPage(id)}
          >
            <Icon size={17} />
            {label}
          </button>
        ))}

        <button
          type="button"
          className="fw-settings-button"
          onClick={() => navigate("/settings")}
        >
          <Settings size={17} />
          Settings
        </button>
      </nav>

      <div className="fw-sidebar-foot">
        Right Vessel.
        <br />
        Right Port.
        <br />
        Right Time.
      </div>

      <button
        type="button"
        className="fw-logout-button"
        onClick={() => navigate("/login")}
      >
        <LogOut size={17} />
        Logout
      </button>
    </aside>
  );
}
