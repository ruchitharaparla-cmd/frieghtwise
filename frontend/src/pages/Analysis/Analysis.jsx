import React from "react";
import "./Analysis.css";

import RecommendationCard from "../../components/analysis/RecommendationCard";
import ForecastCard from "../../components/analysis/ForecastCard";
import CostBreakdown from "../../components/analysis/CostBreakdown";
import RiskScore from "../../components/analysis/RiskScore";
import DelayPrediction from "../../components/analysis/DelayPrediction";
import ReasonList from "../../components/analysis/ReasonList";

const Icon = ({ children, size = 20 }) => (
  <span
    className="icon"
    style={{
      width: size,
      height: size,
      fontSize: size * 0.75,
    }}
  >
    {children}
  </span>
);

function Sidebar() {
  return (
    <aside className="analysis-sidebar">
      <div className="brand">
        <div className="brand-logo">⚓</div>

        <div className="brand-name">FREIGHTWISE</div>

        <div className="brand-tagline">
          Navigate Smarter.
          <br />
          Charter Better.
        </div>
      </div>

      <nav className="side-nav">
        <a href="/" className="side-item">
          <Icon>⌂</Icon>
          <span>Dashboard</span>
        </a>

        <a href="/new-voyage" className="side-item">
          <Icon>➤</Icon>
          <span>New Voyage</span>
        </a>

        <a href="/analysis" className="side-item active">
          <Icon>▥</Icon>
          <span>Analysis</span>
        </a>

        <a href="/vessels" className="side-item">
          <Icon>⚓</Icon>
          <span>Vessels</span>
        </a>

        <a href="/ports" className="side-item">
          <Icon>♙</Icon>
          <span>Ports</span>
        </a>

        <a href="/simulation" className="side-item">
          <Icon>⟳</Icon>
          <span>Simulation</span>
        </a>

        <a href="/settings" className="side-item">
          <Icon>⚙</Icon>
          <span>Settings</span>
        </a>
      </nav>

      <div className="sidebar-bottom">
        <div className="engine-status">
          <div className="engine-title">
            <span className="online-dot" />
            AI Engine Online
          </div>

          <div className="engine-update">
            Data updated
            <br />
            <strong>2 min ago</strong>
          </div>
        </div>

        <div className="sidebar-wave" />

        <div className="sidebar-quote">
          “Smarter Decisions
          <br />
          for a Greener
          <br />
          Indian Maritime Future.”
        </div>
      </div>
    </aside>
  );
}

function Topbar() {
  return (
    <header className="analysis-topbar">
      <div className="search-box">
        <span className="search-icon">⌕</span>

        <input
          type="text"
          placeholder="Search ports, vessels, routes..."
        />
      </div>

      <div className="topbar-right">
        <div className="notification">
          ♧
          <span className="notification-count">3</span>
        </div>

        <div className="profile-divider" />

        <div className="profile">
          <div className="profile-avatar">K</div>
          <span>User</span>
          <span className="profile-arrow">⌄</span>
        </div>
      </div>
    </header>
  );
}

function VoyageHeader() {
  return (
    <section className="voyage-header">
      <div>
        <h1>Voyage Analysis – 75,000 MT Coal</h1>

        <div className="voyage-route">
          <span>
            ⚓ <strong>Hay Point, Australia</strong>
          </span>

          <span className="route-arrow">→</span>

          <span>
            <strong>Paradip, India</strong>
          </span>

          <span className="calendar-icon">▣</span>

          <span>
            <strong>12 – 18 Sep 2026</strong>
          </span>
        </div>
      </div>

      <div className="header-ship">
        <div className="header-date">
          Mon, 25 Aug 2026&nbsp;&nbsp; | &nbsp;&nbsp;14:32 IST
        </div>

        <div className="header-ship-image">
          <div className="ship-shape">🚢</div>
        </div>

        <div className="header-message">
          <strong>Right Vessel.</strong>
          <br />
          <strong>Right Port. Right Time.</strong>
          <br />
          <strong>Lower Cost. Lower Risk.</strong>
        </div>
      </div>
    </section>
  );
}

function CongestionTrend() {
  const ports = [
    ["Kolkata", 12],
    ["Paradip", 32],
    ["Vizag", 20],
    ["Kakinada", 30],
    ["Chennai", 52],
    ["Krishnapatnam", 26],
  ];

  return (
    <section className="panel congestion-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">▥</span>
          Port Congestion Trend
        </div>
      </div>

      <div className="bar-chart">
        <div className="bar-grid">
          <span>60</span>
          <span>40</span>
          <span>20</span>
          <span>0</span>
        </div>

        <div className="bars">
          {ports.map(([name, value], index) => (
            <div className="bar-column" key={name}>
              <div
                className={`bar bar-${index}`}
                style={{
                  height: `${value * 1.45}px`,
                }}
              />

              <span>{name}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Analysis() {
  return (
    <div className="analysis-page">
      <Sidebar />

      <div className="analysis-shell">
        <Topbar />

        <main className="analysis-main">
          <VoyageHeader />

          <RecommendationCard />

          <div className="analysis-row top-row">
            <ForecastCard />
            <CostBreakdown />
          </div>

          <div className="analysis-row bottom-row">
            <RiskScore />
            <DelayPrediction />
            <CongestionTrend />
            <ReasonList />
          </div>

          <div className="analysis-bottom-space" />
        </main>
      </div>
    </div>
  );
}