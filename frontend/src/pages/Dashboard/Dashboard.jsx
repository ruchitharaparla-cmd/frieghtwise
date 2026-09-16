import React from "react";
import {
  ArrowUpRight,
  Ship,
  Anchor,
  Clock3,
  TrendingUp,
  ShieldCheck,
  BarChart3,
} from "lucide-react";

import Card from "../../components/common/Card";
import Badge from "../../components/common/Badge";
import Metric from "../../components/common/Metric";
import SectionTitle from "../../components/common/SectionTitle";
import PageContainer from "../../components/common/PageContainer";

const A = "/assets/";

const voyage = {
  vessel: "MV Eastern Star",
  route: "Visakhapatnam → Singapore",
  cargo: "Iron Ore",
  dwt: "82,000 DWT",
  etd: "24 Sep 2026",
  eta: "02 Oct 2026",
  status: "Planning",
};

export default function Dashboard({ go }) {
  return (
    <PageContainer
      title="Dashboard"
      subtitle="Monitor your freight operations, forecasts, and voyage performance."
    >
      <div className="fw-dashboard-grid">
        <Card className="fw-hero-card">
          <div className="fw-hero-content">
            <div>
              <Badge tone="teal">Active planning</Badge>

              <h2 className="fw-hero-title">
                Plan smarter.
                <br />
                Ship better.
              </h2>

              <p className="fw-hero-description">
                AI-powered freight forecasting and vessel chartering for
                India's East Coast ports.
              </p>

              <button
                className="fw-primary-btn"
                onClick={() => go("new-voyage")}
              >
                Create new voyage
                <ArrowUpRight size={17} />
              </button>
            </div>

            <div className="fw-hero-visual">
              <img
                src={`${A}ship-hero.png`}
                alt="Cargo vessel"
                onError={(event) => {
                  event.currentTarget.style.display = "none";
                }}
              />
            </div>
          </div>
        </Card>

        <div className="fw-metrics-grid">
          <Metric
            label="Forecast accuracy"
            value="92.4%"
            sub="+4.8% from last month"
          />

          <Metric
            label="Active voyages"
            value="08"
            sub="03 awaiting approval"
          />

          <Metric
            label="Average savings"
            value="₹18.6L"
            sub="+12.5% this quarter"
          />

          <Metric
            label="Risk exposure"
            value="Low"
            sub="No critical alerts"
          />
        </div>

        <div className="fw-two-column-grid">
          <Card>
            <SectionTitle
              title="Current voyage"
              right={
                <button
                  className="fw-text-btn"
                  onClick={() => go("new-voyage")}
                >
                  View details
                  <ArrowUpRight size={15} />
                </button>
              }
            />

            <div className="fw-voyage-heading">
              <div className="fw-vessel-icon">
                <Ship size={24} />
              </div>

              <div>
                <h3>{voyage.vessel}</h3>
                <p>{voyage.route}</p>
              </div>

              <Badge tone="teal">{voyage.status}</Badge>
            </div>

            <div className="fw-voyage-details">
              <div>
                <span className="fw-detail-label">Cargo</span>
                <strong>{voyage.cargo}</strong>
              </div>

              <div>
                <span className="fw-detail-label">Capacity</span>
                <strong>{voyage.dwt}</strong>
              </div>

              <div>
                <span className="fw-detail-label">ETD</span>
                <strong>{voyage.etd}</strong>
              </div>

              <div>
                <span className="fw-detail-label">ETA</span>
                <strong>{voyage.eta}</strong>
              </div>
            </div>

            <div className="fw-route-progress">
              <div className="fw-route-point">
                <span className="fw-route-dot active" />
                <div>
                  <strong>Visakhapatnam</strong>
                  <span>Origin port</span>
                </div>
              </div>

              <div className="fw-route-line">
                <span />
              </div>

              <div className="fw-route-point">
                <span className="fw-route-dot" />
                <div>
                  <strong>Singapore</strong>
                  <span>Destination port</span>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <SectionTitle
              title="Quick actions"
              right={<Badge tone="navy">FreightWise</Badge>}
            />

            <div className="fw-quick-actions">
              <button
                className="fw-quick-action"
                onClick={() => go("analysis")}
              >
                <div className="fw-quick-icon blue">
                  <TrendingUp size={21} />
                </div>

                <div>
                  <strong>View freight forecast</strong>
                  <span>Analyze future freight rates</span>
                </div>

                <ArrowUpRight size={17} />
              </button>

              <button
                className="fw-quick-action"
                onClick={() => go("vessels")}
              >
                <div className="fw-quick-icon teal">
                  <Ship size={21} />
                </div>

                <div>
                  <strong>Explore vessels</strong>
                  <span>Find suitable available vessels</span>
                </div>

                <ArrowUpRight size={17} />
              </button>

              <button
                className="fw-quick-action"
                onClick={() => go("ports")}
              >
                <div className="fw-quick-icon orange">
                  <Anchor size={21} />
                </div>

                <div>
                  <strong>Check port conditions</strong>
                  <span>Review port restrictions and waiting time</span>
                </div>

                <ArrowUpRight size={17} />
              </button>

              <button
                className="fw-quick-action"
                onClick={() => go("simulation")}
              >
                <div className="fw-quick-icon purple">
                  <BarChart3 size={21} />
                </div>

                <div>
                  <strong>Run simulation</strong>
                  <span>Compare voyage cost scenarios</span>
                </div>

                <ArrowUpRight size={17} />
              </button>
            </div>
          </Card>
        </div>

        <Card>
          <SectionTitle
            title="Operational overview"
            right={
              <button className="fw-text-btn" onClick={() => go("analysis")}>
                Open analytics
                <ArrowUpRight size={15} />
              </button>
            }
          />

          <div className="fw-overview-grid">
            <div className="fw-overview-item">
              <div className="fw-overview-icon">
                <Clock3 size={20} />
              </div>

              <div>
                <span>Average port waiting time</span>
                <strong>18.6 hrs</strong>
                <small>↓ 8.2% compared to last month</small>
              </div>
            </div>

            <div className="fw-overview-item">
              <div className="fw-overview-icon">
                <ShieldCheck size={20} />
              </div>

              <div>
                <span>Voyages with low risk</span>
                <strong>94%</strong>
                <small>Based on current route conditions</small>
              </div>
            </div>

            <div className="fw-overview-item">
              <div className="fw-overview-icon">
                <TrendingUp size={20} />
              </div>

              <div>
                <span>Forecast trend</span>
                <strong>Stable</strong>
                <small>Freight rates expected to remain steady</small>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </PageContainer>
  );
}