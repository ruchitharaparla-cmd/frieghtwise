import React, { useState } from "react";
import {
  LayoutDashboard, PlusCircle, BarChart3, Ship, Anchor, FlaskConical,
  Search, Bell, ChevronRight, ArrowUpRight, Play, CheckCircle2
} from "lucide-react";
import "./FreightWiseWidget.css";

const A = "/assets/";
const voyage = {
  route: "Australia → East Coast India",
  vessel: "MV Ocean Pride",
  vesselClass: "Capesize",
  port: "Dampier → Paradip",
  charter: "12–16 Sep 2026",
  arrival: "20 Sep 2026",
  cost: "$1.84M",
  risk: "Low",
};

function Card({ children, className = "" }) {
  return <section className={`fw-card ${className}`}>{children}</section>;
}
function Badge({ children, tone = "navy" }) {
  return <span className={`fw-badge ${tone}`}>{children}</span>;
}
function Metric({ label, value, sub }) {
  return <div className="fw-metric"><span>{label}</span><b>{value}</b>{sub && <small>{sub}</small>}</div>;
}
function SectionTitle({ title, right }) {
  return <div className="fw-section-title"><h3>{title}</h3>{right}</div>;
}
function Page({ title, subtitle, children }) {
  return <main className="fw-main">
    <div className="fw-page-title"><div><h1>{title}</h1><p>{subtitle}</p></div><span>MARITIME INTELLIGENCE</span></div>
    {children}
  </main>;
}
function Field({ label, value = "Select", placeholder }) {
  return <label className="fw-field"><span>{label}</span><div>{value || placeholder}<ChevronRight size={13}/></div></label>;
}
function Step({ number, title, children }) {
  return <section className="fw-step"><h3><i>{number}</i>{title}</h3><div className="fw-field-grid">{children}</div></section>;
}
function Cost({ label, value, strong }) {
  return <div className={`fw-cost ${strong ? "strong" : ""}`}><span>{label}</span><b>{value}</b></div>;
}
function Risk({ label, value, tone = "teal" }) {
  return <div className="fw-risk"><span>{label}</span><Badge tone={tone}>{value}</Badge></div>;
}

function Sidebar({ page, setPage }) {
  const items = [
    ["dashboard", "Dashboard", LayoutDashboard],
    ["new-voyage", "New Voyage", PlusCircle],
    ["analysis", "Analysis", BarChart3],
    ["simulation", "Simulation", FlaskConical],
    ["vessels", "Vessels", Ship],
    ["ports", "Ports", Anchor],
  ];
  return <aside className="fw-sidebar">
    <div className="fw-brand">
      <img src={`${A}freightwise-logo.png`} alt="FreightWise logo" />
      <div><strong>FreightWise</strong><small>Maritime Intelligence</small></div>
    </div>
    <nav>{items.map(([id, label, Icon]) =>
      <button key={id} className={page === id ? "active" : ""} onClick={() => setPage(id)}>
        <Icon size={17}/>{label}
      </button>
    )}</nav>
    <div className="fw-sidebar-foot">Right Vessel.<br/>Right Port.<br/>Right Time.</div>
  </aside>;
}
function Header() {
  return <header className="fw-header">
    <div className="fw-search"><Search size={15}/>Search ports, vessels, routes...</div>
    <div className="fw-header-right"><span>Fri, 12 Sep 2026</span><Bell size={16}/><div className="fw-avatar">K</div><span>Keerthi</span><ChevronRight size={14}/></div>
  </header>;
}

function Dashboard({ go }) {
  return <Page title="Welcome back, Keerthi." subtitle="Here's your latest voyage recommendation and market overview.">
    <Card className="fw-hero-card">
     <img
  className="fw-hero-image"
  src={`${A}port-terminal.png`}
  alt="Cargo vessel at a port during sunset"
/>
      <div className="fw-hero-overlay"><span>FREIGHTWISE</span><h2>Smarter Chartering<br/>for a Stronger Tomorrow</h2><p>Better data. Lower costs. Safer voyages.</p></div>
    </Card>
    <Card className="fw-recommend">
      <div className="fw-eyebrow">RECOMMENDED VOYAGE <Badge>RECOMMENDED</Badge></div>
      <h2>{voyage.route}</h2>
      <div className="fw-metric-grid">
        <Metric label="Vessel" value={voyage.vessel} sub={voyage.vesselClass}/>
        <Metric label="Port Plan" value={voyage.port}/>
        <Metric label="Charter Window" value={voyage.charter}/>
        <Metric label="Estimated Cost" value={voyage.cost}/>
        <Metric label="Overall Risk" value={voyage.risk}/>
      </div>
      <button className="fw-primary" onClick={() => go("analysis")}>View Full Analysis <ArrowUpRight size={15}/></button>
    </Card>
    <div className="fw-kpis"><Metric label="Active Voyages" value="8"/><Metric label="Upcoming Arrivals" value="3"/><Metric label="Total Freight Exposure" value="$12.4M"/><Metric label="Alerts" value="2"/></div>
    <Card><SectionTitle title="Freight Rate Trend" right="Last 3 Months"/>
      <div className="fw-trend"><div className="fw-chart"><svg viewBox="0 0 620 150" preserveAspectRatio="none"><polyline points="0,45 80,58 150,55 230,78 300,86 370,82 450,92" fill="none" stroke="#17324D" strokeWidth="3"/><polyline points="450,92 520,88 620,90" fill="none" stroke="#8A99A8" strokeWidth="3" strokeDasharray="7 7"/><line x1="450" y1="10" x2="450" y2="140" stroke="#D9E0E6"/></svg><div className="fw-chart-axis"><span>Jun</span><span>Jul</span><span>Aug</span><span>Sep</span></div></div><div className="fw-rate"><b>$24.8 / MT</b><span>Current Rate</span><b>$25.6 / MT</b><span>Previous Rate</span><Badge tone="teal">−3.1%</Badge></div></div>
    </Card>
  </Page>;
}

function NewVoyage({ go }) {
  return <Page title="New Voyage" subtitle="Enter voyage requirements to get AI-powered recommendations.">
    <Card><Step number="1" title="Cargo Details"><Field label="Voyage Name" placeholder="Australia Coal Import — Sep 2026"/><Field label="Cargo Type" value="Coal"/><Field label="Cargo Quantity (MT)" value="75000"/></Step>
      <Step number="2" title="Route Details"><Field label="Origin Country" value="Australia"/><Field label="Destination Region" value="East Coast India"/><Field label="Loading Port (Optional)"/><Field label="Discharge Port (Optional)"/></Step>
      <Step number="3" title="Delivery Requirement"><Field label="Required Arrival Date" value="20 Sep 2026"/><Field label="Latest Acceptable Arrival"/><Field label="Flexibility" value="Normal"/></Step>
      <div className="fw-actions"><button className="fw-primary" onClick={() => go("analysis")}>Find Best Vessel, Port & Charter Time <ChevronRight size={16}/></button></div>
    </Card>
  </Page>;
}

function Analysis({ go }) {
  return <Page title="Voyage Analysis" subtitle="AI-powered recommendation based on your voyage inputs.">
    <div className="fw-analysis-top">
      <Card className="fw-score-card"><div className="fw-eyebrow">OVERALL RECOMMENDATION</div><Badge tone="teal">RECOMMENDED</Badge><div className="fw-score">86<span>/100</span></div><p>Meets delivery deadline with lowest estimated total cost.</p></Card>
      <Card><div className="fw-eyebrow">RECOMMENDED VESSEL</div><h3>{voyage.vessel}</h3><p>Capesize · 180,000 DWT · LOA 292 m</p><button className="fw-secondary" onClick={() => go("vessels")}>View Vessel Details</button></Card>
      <Card><div className="fw-eyebrow">RECOMMENDED PORT PLAN</div><h3>{voyage.port}</h3><p>Loading: Dampier · Discharge: Paradip</p><button className="fw-secondary" onClick={() => go("ports")}>View Port Details</button></Card>
      <Card><div className="fw-eyebrow">RECOMMENDED CHARTER WINDOW</div><h3>{voyage.charter}</h3><p>Expected arrival: {voyage.arrival}</p><Badge tone="teal">ON TIME</Badge></Card>
    </div>
    <div className="fw-two-col"><Card><SectionTitle title="Cost Analysis"/><Cost label="Freight Cost" value="$1,356,000"/><Cost label="Bunker Cost" value="$285,000"/><Cost label="Port Cost" value="$92,000"/><Cost label="Demurrage (Est.)" value="$64,500"/><hr/><Cost label="Total Landed Cost" value="$1,842,500" strong/></Card><Card><SectionTitle title="Risk Assessment"/><Risk label="Overall Risk" value="Low"/><Risk label="Delay Risk" value="Low"/><Risk label="Port Congestion" value="Medium" tone="sand"/><Risk label="Weather Risk" value="Low"/><Risk label="Freight Price Risk" value="Medium" tone="sand"/></Card></div>
    <Card><SectionTitle title="Why This Recommendation?"/><ol className="fw-reasons"><li>Meets the required arrival date.</li><li>Lowest estimated total landed cost.</li><li>Vessel capacity matches cargo quantity.</li><li>Ports have acceptable waiting time.</li><li>Lower delay risk compared to alternatives.</li></ol></Card>
    <Card><SectionTitle title="Alternative Options" right={<button className="fw-secondary" onClick={() => go("simulation")}>Compare in Simulation</button>}/><div className="fw-alt-row"><b>Cheapest</b><span>MV Frontier</span><span>$1.96M</span><span>Medium Risk</span></div><div className="fw-alt-row"><b>Fastest</b><span>MV Blue Horizon</span><span>$2.04M</span><span>Low Risk</span></div></Card>
  </Page>;
}

function Vessels({ go }) {
  const rows = [["MV Ocean Pride","Capesize","180,000","292","Available"],["MV Blue Horizon","Panamax","82,000","229","Available"],["MV Sea Crown","Supramax","58,000","190","In Transit"],["MV Eastern Star","Handysize","37,000","180","Available"],["MV Unity","Panamax","76,000","225","Available"]];
  return <Page title="Vessels" subtitle="Explore available vessels and their specifications."><Card><div className="fw-directory-head"><div className="fw-search inline"><Search size={15}/>Search vessel name, class...</div><select><option>All Vessel Classes</option></select></div><div className="fw-feature-image"><img src={`${A}cargo-vessel.png`} alt="Cargo vessel"/></div><table><thead><tr><th>#</th><th>Vessel</th><th>Class</th><th>DWT</th><th>LOA (m)</th><th>Status</th><th></th></tr></thead><tbody>{rows.map((r,i)=><tr key={r[0]}><td>{i+1}</td><td><b>{r[0]}</b></td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td><Badge tone={r[4] === "Available" ? "teal" : "sand"}>{r[4]}</Badge></td><td><button className="fw-link" onClick={() => go("new-voyage")}>Use in Voyage</button></td></tr>)}</tbody></table></Card></Page>;
}

function Ports({ go }) {
  const rows = [["Paradip Port","INPRP","Odisha","16.0","28","Operational"],["Vizag Port","INVTZ","Andhra Pradesh","16.5","36","Operational"],["Gangavaram Port","INGWV","Andhra Pradesh","18.0","42","Congested"],["Kakinada Port","INKAK","Andhra Pradesh","16.0","30","Operational"],["Chennai Port","INMAA","Tamil Nadu","14.5","26","Operational"]];
  return <Page title="Ports" subtitle="Explore port capabilities and operational status."><Card><div className="fw-directory-head"><div className="fw-search inline"><Search size={15}/>Search port name, code...</div><select><option>All Countries</option></select></div><div className="fw-port-image"><img src={`${A}port-terminal.png`} alt="Port terminal"/></div><table><thead><tr><th>#</th><th>Port Name</th><th>Code</th><th>State</th><th>Max Draft</th><th>Avg Waiting</th><th>Status</th><th></th></tr></thead><tbody>{rows.map((r,i)=><tr key={r[0]}><td>{i+1}</td><td><b>{r[0]}</b></td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]} m</td><td>{r[4]} h</td><td><Badge tone={r[5] === "Operational" ? "teal" : "sand"}>{r[5]}</Badge></td><td><button className="fw-link" onClick={() => go("new-voyage")}>Use as Destination</button></td></tr>)}</tbody></table></Card></Page>;
}

function Simulation({ go }) {
  const rows = [["Recommended","MV Ocean Pride","Dampier → Paradip","$1.84M","Low","20 Sep"],["Cheapest","MV Frontier","Dampier → Paradip","$1.96M","Medium","24 Sep"],["Fastest","MV Blue Horizon","Dampier → Vizag","$2.04M","Low","18 Sep"],["Lowest Risk","MV Unity","Newcastle → Paradip","$1.92M","Low","22 Sep"]];
  return <Page title="Simulation" subtitle="Compare scenarios to evaluate cost, risk and delivery time."><div className="fw-two-col"><Card><SectionTitle title="Scenario Inputs"/><Field label="Vessel Class" value="Capesize"/><Field label="Alternative Loading Port"/><Field label="Alternative Discharge Port"/><Field label="Charter Start Date"/><button className="fw-primary fw-full" onClick={() => go("analysis")}><Play size={15}/> Run Simulation</button></Card><Card><SectionTitle title="Scenario Comparison"/><div className="fw-scenario fw-scenario-head"><b>Option</b><b>Vessel</b><b>Port Route</b><b>Total Cost</b><b>Risk</b><b>Arrival</b></div>{rows.map(r=><div className="fw-scenario" key={r[0]}>{r.map((x,i)=><span key={i}>{x}</span>)}</div>)}</Card></div><Card><SectionTitle title="Key Takeaway"/><p>The recommended option offers the best balance of cost, risk and delivery time.</p></Card></Page>;
}

export default function FreightWiseWidget() {
  const [page, setPage] = useState("dashboard");
  return <div className="fw-shell"><Sidebar page={page} setPage={setPage}/><div className="fw-content"><Header/>{page === "dashboard" && <Dashboard go={setPage}/>} {page === "new-voyage" && <NewVoyage go={setPage}/>} {page === "analysis" && <Analysis go={setPage}/>} {page === "vessels" && <Vessels go={setPage}/>} {page === "ports" && <Ports go={setPage}/>} {page === "simulation" && <Simulation go={setPage}/>}</div></div>;
}
