import React, { useState } from "react";
import "./NewVoyage.css";
import shipImage from "../../assets/images/ship.png";
import portImage from "../../assets/images/port.png";

const Icon = ({ type }) => {
  const icons = {
    home: "⌂",
    voyage: "➤",
    analysis: "▥",
    vessel: "♜",
    port: "♙",
    simulation: "⟳",
    settings: "⚙",
    cargo: "▣",
    route: "⌖",
    calendar: "▣",
    ship: "♜",
    document: "▤",
    bulb: "💡",
    search: "⌕",
    bell: "♧",
    arrow: "→",
  };

  return <span className={`icon icon-${type}`}>{icons[type]}</span>;
};

function NewVoyage() {
  const [cargoType, setCargoType] = useState("Coal");
  const [quantity, setQuantity] = useState("75000");
  const [loadingPort, setLoadingPort] = useState("Hay Point, Australia");
  const [dischargePort, setDischargePort] = useState("Paradip, India");
  const [arrivalDate, setArrivalDate] = useState("");
  const [flexibleDate, setFlexibleDate] = useState(false);

  const [vesselType, setVesselType] = useState("Bulk Carrier");
  const [draft, setDraft] = useState("14.5");
  const [loa, setLoa] = useState("200");
  const [beam, setBeam] = useState("32");

  const [weather, setWeather] = useState("Normal");
  const [contract, setContract] = useState("Spot");
  const [priority, setPriority] = useState("Lowest Cost");

  const [previousVoyage, setPreviousVoyage] = useState(true);
  const [alternativeRoutes, setAlternativeRoutes] = useState(true);
  const [whatIf, setWhatIf] = useState(false);

  const [message, setMessage] = useState("");

  const handleAnalysis = () => {
    setMessage(
      `Analysis started for ${quantity || "0"} MT ${cargoType} from ${loadingPort} to ${dischargePort}.`
    );

    setTimeout(() => {
      setMessage("");
    }, 4000);
  };

  const resetForm = () => {
    setCargoType("Coal");
    setQuantity("75000");
    setLoadingPort("Hay Point, Australia");
    setDischargePort("Paradip, India");
    setArrivalDate("");
    setFlexibleDate(false);

    setVesselType("Bulk Carrier");
    setDraft("14.5");
    setLoa("200");
    setBeam("32");

    setWeather("Normal");
    setContract("Spot");
    setPriority("Lowest Cost");

    setPreviousVoyage(true);
    setAlternativeRoutes(true);
    setWhatIf(false);

    setMessage("");
  };

  return (
    <div className="freightwise-app">

      {/* ================= SIDEBAR ================= */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-logo">
            ⚓
          </div>

          <div className="brand-name">
            FREIGHTWISE
          </div>

          <div className="brand-tagline">
            Navigate Smarter.
            <br />
            Charter Better.
          </div>
        </div>

        <nav className="sidebar-nav">

          <button className="nav-item">
            <Icon type="home" />
            <span>Dashboard</span>
          </button>

          <button className="nav-item active">
            <Icon type="voyage" />
            <span>New Voyage</span>
          </button>

          <button className="nav-item">
            <Icon type="analysis" />
            <span>Analysis</span>
          </button>

          <button className="nav-item">
            <Icon type="vessel" />
            <span>Vessels</span>
          </button>

          <button className="nav-item">
            <Icon type="port" />
            <span>Ports</span>
          </button>

          <button className="nav-item">
            <Icon type="simulation" />
            <span>Simulation</span>
          </button>

          <button className="nav-item">
            <Icon type="settings" />
            <span>Settings</span>
          </button>

        </nav>

        <div className="engine-status">
          <div className="engine-title">
            <span className="online-dot"></span>
            AI Engine Online
          </div>

          <div className="engine-text">
            Data updated
            <br />
            2 min ago
          </div>
        </div>

        <div className="sidebar-bottom">
          <p>
            "Right Data.
            <br />
            Smarter Decisions.
            <br />
            Greener Seas."
          </p>
        </div>

      </aside>

      {/* ================= MAIN AREA ================= */}
      <main className="main-area">

        {/* TOP BAR */}
        <header className="topbar">

          <div className="search-box">
            <Icon type="search" />
            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />
          </div>

          <div className="topbar-right">

            <div className="notification">
              <span>♧</span>
              <b>3</b>
            </div>

            <div className="user-profile">
              <div className="avatar">K</div>
              <span>User</span>
              <span className="dropdown-arrow">⌄</span>
            </div>

          </div>

        </header>

        {/* ================= HERO ================= */}
        <section className="page-hero">

          <div className="hero-text">
            <h1>Plan a New Voyage</h1>

            <p>
              Provide voyage details to get AI-powered recommendations
            </p>
          </div>

          <div className="hero-image">
            <img
            src={shipImage}
            alt="Cargo ship"
            />
            <div className="hero-quote">
              "Better Planning
              <br />
              Smarter Chartering
              <br />
              A Stronger India."
              </div>
              </div>

        </section>

        {/* ================= STEPS ================= */}
        <div className="steps-container">

          <div className="step active">
            <span>1</span>
            <strong>Cargo Details</strong>
          </div>

          <div className="step-line"></div>

          <div className="step">
            <span>2</span>
            <strong>Route</strong>
          </div>

          <div className="step-line"></div>

          <div className="step">
            <span>3</span>
            <strong>Voyage Dates</strong>
          </div>

          <div className="step-line"></div>

          <div className="step">
            <span>4</span>
            <strong>Vessel Requirements</strong>
          </div>

          <div className="step-line"></div>

          <div className="step">
            <span>5</span>
            <strong>Additional Constraints</strong>
          </div>

          <div className="step-line"></div>

          <div className="step">
            <span>6</span>
            <strong>Review</strong>
          </div>

        </div>

        {/* ================= CONTENT GRID ================= */}
        <section className="content-grid">

          {/* CARD 1 */}
          <div className="form-card">

            <div className="card-heading">
              <div className="card-icon">
                <Icon type="cargo" />
              </div>

              <div>
                <h2>1. Cargo Details</h2>
                <p>Tell us what you want to ship</p>
              </div>
            </div>

            <div className="form-row">

              <div className="field">
                <label>
                  Cargo Type <span>*</span>
                </label>

                <select
                  value={cargoType}
                  onChange={(e) => setCargoType(e.target.value)}
                >
                  <option>Coal</option>
                  <option>Iron Ore</option>
                  <option>Fertilizer</option>
                  <option>Grain</option>
                  <option>Other Bulk Cargo</option>
                </select>
              </div>

              <div className="field">
                <label>
                  Quantity (MT) <span>*</span>
                </label>

                <div className="input-unit">
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                  />
                  <span>MT</span>
                </div>
              </div>

            </div>

            <div className="info-box">
              <b>ⓘ</b>
              Supported: Coal, Iron Ore, Fertilizer, Grain and other bulk
              cargoes.
            </div>

          </div>

          {/* CARD 2 */}
          <div className="form-card">

            <div className="card-heading">
              <div className="card-icon">
                <Icon type="route" />
              </div>

              <div>
                <h2>2. Route</h2>
                <p>Select loading and discharge ports</p>
              </div>
            </div>

            <div className="route-fields">

              <div className="field">
                <label>
                  Loading Port <span>*</span>
                </label>

                <select
                  value={loadingPort}
                  onChange={(e) => setLoadingPort(e.target.value)}
                >
                  <option>Hay Point, Australia</option>
                  <option>Newcastle, Australia</option>
                  <option>Gladstone, Australia</option>
                  <option>Richards Bay, South Africa</option>
                </select>
              </div>

              <div className="swap-button">⇄</div>

              <div className="field">
                <label>
                  Discharge Port <span>*</span>
                </label>

                <select
                  value={dischargePort}
                  onChange={(e) => setDischargePort(e.target.value)}
                >
                  <option>Paradip, India</option>
                  <option>Visakhapatnam, India</option>
                  <option>Kakinada, India</option>
                  <option>Chennai, India</option>
                  <option>Kolkata, India</option>
                </select>
              </div>

            </div>

            <div className="route-info">
              <span className="route-icon">♜</span>

              <div>
                <strong>Distance (approx.): 5,620 nautical miles</strong>
                <br />
                Estimated voyage duration: 24 – 28 days
              </div>
            </div>

          </div>

          {/* CARD 3 */}
          <div className="form-card">

            <div className="card-heading">
              <div className="card-icon">
                <Icon type="calendar" />
              </div>

              <div>
                <h2>3. Voyage Dates</h2>
                <p>When do you need the vessel?</p>
              </div>
            </div>

            <div className="field">

              <label>
                Expected Arrival Date <span>*</span>
              </label>

              <input
                className="date-input"
                type="date"
                value={arrivalDate}
                onChange={(e) => setArrivalDate(e.target.value)}
              />

            </div>

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={flexibleDate}
                onChange={(e) => setFlexibleDate(e.target.checked)}
              />

              <span>Flexible date</span>
            </label>

            <div className="info-box">
              <b>ⓘ</b>
              You can select a fixed arrival date or allow flexibility for
              better recommendations.
            </div>

          </div>

          {/* CARD 4 */}
          <div className="form-card">

            <div className="card-heading">
              <div className="card-icon">
                <Icon type="ship" />
              </div>

              <div>
                <h2>4. Vessel Requirements</h2>
                <p>Specify your vessel preferences</p>
              </div>
            </div>

            <div className="form-row">

              <div className="field">
                <label>Vessel Type <span>*</span></label>

                <select
                  value={vesselType}
                  onChange={(e) => setVesselType(e.target.value)}
                >
                  <option>Bulk Carrier</option>
                  <option>Panamax</option>
                  <option>Supramax</option>
                  <option>Capesize</option>
                </select>
              </div>

              <div className="field">
                <label>Maximum Draft (m)</label>

                <div className="input-unit">
                  <input
                    type="number"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                  />
                  <span>m</span>
                </div>
              </div>

            </div>

            <div className="form-row">

              <div className="field">
                <label>Maximum LOA (m)</label>

                <div className="input-unit">
                  <input
                    type="number"
                    value={loa}
                    onChange={(e) => setLoa(e.target.value)}
                  />
                  <span>m</span>
                </div>
              </div>

              <div className="field">
                <label>Maximum Beam (m)</label>

                <div className="input-unit">
                  <input
                    type="number"
                    value={beam}
                    onChange={(e) => setBeam(e.target.value)}
                  />
                  <span>m</span>
                </div>
              </div>

            </div>

            <div className="info-box">
              <b>ⓘ</b>
              Enter minimum requirements. We will match the best available
              vessels.
            </div>

          </div>

          {/* CARD 5 */}
          <div className="form-card">

            <div className="card-heading">
              <div className="card-icon">
                <Icon type="document" />
              </div>

              <div>
                <h2>5. Additional Constraints</h2>
                <p>Add any operational constraints</p>
              </div>
            </div>

            <div className="constraint-layout">

              <div>

                <div className="field">
                  <label>Weather Tolerance</label>

                  <select
                    value={weather}
                    onChange={(e) => setWeather(e.target.value)}
                  >
                    <option>Normal</option>
                    <option>Low Risk Preferred</option>
                    <option>High Risk Tolerant</option>
                  </select>
                </div>

                <div className="field">
                  <label>Contract Type</label>

                  <select
                    value={contract}
                    onChange={(e) => setContract(e.target.value)}
                  >
                    <option>Spot</option>
                    <option>Time Charter</option>
                    <option>COA</option>
                  </select>
                </div>

                <div className="field">
                  <label>Priority</label>

                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                  >
                    <option>Lowest Cost</option>
                    <option>Lowest Risk</option>
                    <option>Balanced</option>
                    <option>Fastest Delivery</option>
                  </select>
                </div>

              </div>

              <div className="check-list">

                <label className="check-option">
                  <input
                    type="checkbox"
                    checked={previousVoyage}
                    onChange={(e) => setPreviousVoyage(e.target.checked)}
                  />
                  <span>
                    Consider previous voyage /
                    <br />
                    positioning
                  </span>
                </label>

                <label className="check-option">
                  <input
                    type="checkbox"
                    checked={alternativeRoutes}
                    onChange={(e) =>
                      setAlternativeRoutes(e.target.checked)
                    }
                  />
                  <span>Include alternative routes</span>
                </label>

                <label className="check-option">
                  <input
                    type="checkbox"
                    checked={whatIf}
                    onChange={(e) => setWhatIf(e.target.checked)}
                  />
                  <span>Enable what-if analysis</span>
                </label>

              </div>

            </div>

          </div>

          {/* CARD 6 */}
          <div className="form-card tips-card">

            <div className="card-heading">

              <div className="bulb-icon">
                <Icon type="bulb" />
              </div>

              <div>
                <h2>Tips for Better Recommendations</h2>
              </div>

            </div>

            <ul className="tips-list">
              <li>Provide accurate cargo details</li>
              <li>Select flexible dates for more options</li>
              <li>Include any draft or port restrictions</li>
              <li>Consider alternative routes</li>
              <li>Enable what-if analysis to compare scenarios</li>
            </ul>

            <div className="tips-image"
            style={{ backgroundImage: `url(${portImage})` }}>
              <div className="tips-quote">
                "Connecting Global Resources
                <br />
                to India's Growth"
              </div>
            </div>

          </div>

        </section>

        {/* ================= BOTTOM ACTION ================= */}
        <div className="bottom-actions">

          <button
            className="reset-button"
            onClick={resetForm}
          >
            ⟳
            <span>Reset Form</span>
          </button>

          <button
            className="analysis-button"
            onClick={handleAnalysis}
          >
            ✨
            <span>Run FreightWise Analysis</span>
            <span>→</span>
          </button>

        </div>

        {message && (
          <div className="success-message">
            ✓ {message}
          </div>
        )}

      </main>
    </div>
  );
}

export default NewVoyage;