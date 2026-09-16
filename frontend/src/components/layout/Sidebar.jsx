import React from "react";
import {
  LayoutDashboard,
  PlusCircle,
  BarChart3,
  Ship,
  Anchor,
  FlaskConical,
  Settings,
} from "lucide-react";

const navigationItems = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    id: "new-voyage",
    label: "New Voyage",
    icon: PlusCircle,
  },
  {
    id: "analysis",
    label: "Analysis",
    icon: BarChart3,
  },
  {
    id: "vessels",
    label: "Vessels",
    icon: Ship,
  },
  {
    id: "ports",
    label: "Ports",
    icon: Anchor,
  },
  {
    id: "simulation",
    label: "Simulation",
    icon: FlaskConical,
  },
];

export default function Sidebar({
  page,
  setPage,
  onSettings,
}) {
  return (
    <aside className="fw-sidebar">
      <div className="fw-sidebar-brand">
        <div className="fw-sidebar-brand-icon">
          <Anchor size={25} strokeWidth={2} />
        </div>

        <div className="fw-sidebar-brand-text">
          <strong>FreightWise</strong>
          <span>AI MARITIME INTELLIGENCE</span>
        </div>
      </div>

      <nav className="fw-sidebar-nav">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = page === item.id;

          return (
            <button
              key={item.id}
              type="button"
              className={`fw-sidebar-link ${
                isActive ? "active" : ""
              }`}
              onClick={() => setPage(item.id)}
            >
              <Icon size={21} strokeWidth={2} />
              <span>{item.label}</span>
            </button>
          );
        })}

        <button
          type="button"
          className={`fw-sidebar-link fw-settings-link ${
            page === "settings" ? "active" : ""
          }`}
          onClick={() => {
            if (onSettings) {
              onSettings();
            } else {
              setPage("settings");
            }
          }}
        >
          <Settings size={21} strokeWidth={2} />
          <span>Settings</span>
        </button>
      </nav>

      <div className="fw-sidebar-footer">
        FreightWise Platform v1.0.0
      </div>
    </aside>
  );
}