import React from "react";
import "./Analysis.css";

/* ---------------- ICONS ---------------- */

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

/* ---------------- SIDEBAR ---------------- */

function Sidebar() {
  return (
    <aside className="analysis-sidebar">
      <div className="brand">
        <div className="brand-logo">
          ⚓
        </div>

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

/* ---------------- TOPBAR ---------------- */

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

/* ---------------- PAGE HEADER ---------------- */

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

/* ---------------- RECOMMENDATION ---------------- */

function RecommendationCard() {
  return (
    <section className="recommendation-card">
      <div className="recommendation-main">
        <div className="recommendation-image">
          <div className="ship-photo">
            🚢
          </div>

          <div className="recommendation-vessel">
            <strong>MV Ocean Star</strong>
            <span>76,000 DWT&nbsp; | &nbsp;Bulk Carrier</span>
          </div>
        </div>

        <div className="recommendation-copy">
          <div className="recommendation-label">
            ✓ &nbsp; FREIGHTWISE RECOMMENDS
          </div>

          <h2>
            Charter MV Ocean Star between
            <br />
            12 – 18 Sep via Paradip Port.
          </h2>

          <p>
            Best balance of cost, risk and availability.
          </p>
        </div>

        <div className="confidence-box">
          <strong>87%</strong>
          <span>Confidence</span>

          <div className="confidence-bar">
            <div style={{ width: "87%" }} />
          </div>
        </div>
      </div>

      <div className="kpi-row">
        <Kpi
          icon="▣"
          title="Expected Total Cost"
          value="₹ 6.42 Cr"
          type="blue"
        />

        <Kpi
          icon="↗"
          title="Expected Savings"
          value="₹ 18.4 L"
          subtitle="vs. current market"
          type="green"
        />

        <Kpi
          icon="✓"
          title="Risk Score"
          value="32 / 100"
          subtitle="Low Risk"
          type="green"
        />

        <Kpi
          icon="◷"
          title="Expected Delay"
          value="2.4 Days"
          type="blue"
        />
      </div>
    </section>
  );
}

function Kpi({ icon, title, value, subtitle, type }) {
  return (
    <div className="kpi-card">
      <div className={`kpi-icon ${type}`}>
        {icon}
      </div>

      <div>
        <span className="kpi-title">{title}</span>

        <strong className="kpi-value">{value}</strong>

        {subtitle && (
          <span className="kpi-subtitle">{subtitle}</span>
        )}
      </div>
    </div>
  );
}

/* ---------------- FORECAST CHART ---------------- */

function ForecastChart() {
  return (
    <div className="forecast-chart">
      <div className="chart-y-axis">
        <span>50</span>
        <span>40</span>
        <span>30</span>
        <span>20</span>
        <span>10</span>
      </div>

      <div className="chart-area">
        <div className="chart-grid">
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>

        <div className="today-line">
          <span>Today</span>
        </div>

        <svg
          className="forecast-svg"
          viewBox="0 0 650 260"
          preserveAspectRatio="none"
        >
          <polyline
            className="historical-line"
            points="
              10,90
              65,70
              120,82
              175,112
              230,108
              285,145
              340,128
              395,132
              450,108
            "
          />

          <polyline
            className="forecast-line"
            points="
              450,108
              500,122
              545,140
              590,155
              625,170
            "
          />

          <polyline
            className="confidence-line"
            points="
              450,90
              500,102
              545,115
              590,132
              625,148
            "
          />

          {[10, 65, 120, 175, 230, 285, 340, 395, 450].map(
            (x, index) => (
              <circle
                key={index}
                cx={x}
                cy={
                  [
                    90,
                    70,
                    82,
                    112,
                    108,
                    145,
                    128,
                    132,
                    108,
                  ][index]
                }
                r="4"
                className="history-point"
              />
            )
          )}
        </svg>

        <div className="chart-months">
          <span>Jan</span>
          <span>Feb</span>
          <span>Mar</span>
          <span>Apr</span>
          <span>May</span>
          <span>Jun</span>
          <span>Jul</span>
          <span>Aug</span>
          <span>Sep</span>
          <span>Oct</span>
          <span>Nov</span>
          <span>Dec</span>
        </div>
      </div>
    </div>
  );
}

/* ---------------- FORECAST SECTION ---------------- */

function ForecastSection() {
  return (
    <section className="panel forecast-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">▥</span>
          Freight Forecast
        </div>

        <div className="forecast-tabs">
          <button>7 Days</button>
          <button className="selected">14 Days</button>
          <button>30 Days</button>
        </div>
      </div>

      <div className="forecast-content">
        <ForecastChart />

        <div className="forecast-insight">
          <span>Forecast Insights</span>

          <strong>
            ↓ 4.8%
          </strong>

          <b>Expected decline</b>

          <p>in next 14 days.</p>

          <div className="insight-text">
            Freight rates are projected
            to decrease, driven by
            increased vessel supply
            and lower demand.
          </div>
        </div>
      </div>

      <div className="chart-legend">
        <span>
          <i className="legend-dot historical" />
          Historical
        </span>

        <span>
          <i className="legend-dot forecast" />
          Forecast
        </span>

        <span>
          <i className="legend-box" />
          Confidence Range
        </span>
      </div>
    </section>
  );
}

/* ---------------- COST DONUT ---------------- */

function CostBreakdown() {
  return (
    <section className="panel cost-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">▣</span>
          True Voyage Cost Breakdown
        </div>
      </div>

      <div className="cost-content">
        <div className="donut-wrapper">
          <div className="donut">
            <div className="donut-center">
              <strong>₹ 6.42 Cr</strong>
              <span>Total Expected Cost</span>
            </div>
          </div>
        </div>

        <div className="cost-list">
          <CostRow
            color="blue"
            name="Base Freight"
            value="₹ 4.10 Cr"
            percent="64%"
          />

          <CostRow
            color="orange"
            name="Bunker / Fuel"
            value="₹ 0.82 Cr"
            percent="13%"
          />

          <CostRow
            color="purple"
            name="Port Charges"
            value="₹ 0.46 Cr"
            percent="7%"
          />

          <CostRow
            color="dark-blue"
            name="Expected Demurrage"
            value="₹ 0.36 Cr"
            percent="6%"
          />

          <CostRow
            color="light-blue"
            name="Other Costs"
            value="₹ 0.46 Cr"
            percent="7%"
          />
        </div>

        <div className="hidden-risk">
          <strong>Hidden Cost Risk</strong>

          <span>+8.4%</span>

          <p>
            Due to potential delays,
            weather and port
            congestion.
          </p>
        </div>
      </div>

      <div className="cost-warning">
        <span>!</span>
        Actual costs may vary based on real-time port conditions,
        fuel prices and weather changes.
      </div>
    </section>
  );
}

function CostRow({ color, name, value, percent }) {
  return (
    <div className="cost-row">
      <span className={`cost-dot ${color}`} />
      <span className="cost-name">{name}</span>
      <strong>{value}</strong>
      <small>({percent})</small>
    </div>
  );
}

/* ---------------- RISK ---------------- */

function RiskAnalysis() {
  return (
    <section className="panel risk-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">✓</span>
          Risk Analysis
        </div>
      </div>

      <div className="risk-grid">
        <RiskGauge
          title="Weather Risk"
          value="24%"
          label="Low"
          progress={24}
          type="green"
        />

        <RiskGauge
          title="Port Congestion"
          value="41%"
          label="Moderate"
          progress={41}
          type="orange"
        />

        <RiskGauge
          title="Vessel Availability"
          value="18%"
          label="Low"
          progress={18}
          type="green"
        />
      </div>
    </section>
  );
}

function RiskGauge({
  title,
  value,
  label,
  progress,
  type,
}) {
  return (
    <div className="risk-gauge-card">
      <span>{title}</span>

      <div className={`gauge ${type}`}>
        <div
          className="gauge-progress"
          style={{
            "--progress": `${progress * 1.8}deg`,
          }}
        />
      </div>

      <strong>{value}</strong>

      <b className={type}>{label}</b>
    </div>
  );
}

/* ---------------- DELAY ---------------- */

function DelayPrediction() {
  return (
    <section className="panel delay-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">◷</span>
          Delay Prediction
        </div>
      </div>

      <div className="delay-item">
        <div className="delay-icon blue-bg">◴</div>

        <div>
          <span>Expected Delay</span>
          <strong>2.4 Days</strong>
          <small>(± 1.1 days)</small>
        </div>
      </div>

      <div className="delay-item">
        <div className="delay-icon orange-bg">₹</div>

        <div>
          <span>Expected Demurrage</span>
          <strong>₹ 28.4 Lakhs</strong>
          <small>(± 12.6)</small>
        </div>
      </div>
    </section>
  );
}

/* ---------------- CONGESTION ---------------- */

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

/* ---------------- WHY ---------------- */

function RecommendationReasons() {
  const reasons = [
    "Freight rate expected to decrease moderately",
    "Vessel matches cargo requirement",
    "Paradip has acceptable draft and port infrastructure",
    "Lower congestion compared to alternative ports",
    "Low weather risk during the booking window",
    "Lower expected demurrage",
    "Better overall voyage cost and availability",
  ];

  return (
    <section className="panel why-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">💡</span>
          Why this recommendation?
        </div>
      </div>

      <div className="reason-list">
        {reasons.map((reason) => (
          <div className="reason" key={reason}>
            <span>✓</span>
            <p>{reason}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ---------------- MAIN PAGE ---------------- */

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
            <ForecastSection />
            <CostBreakdown />
          </div>

          <div className="analysis-row bottom-row">
            <RiskAnalysis />
            <DelayPrediction />
            <CongestionTrend />
            <RecommendationReasons />
          </div>

          {/* Extra spacing so the page has comfortable scrolling */}
          <div className="analysis-bottom-space" />
        </main>
      </div>
    </div>
  );
}