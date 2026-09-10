import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./NewVoyage.css";
import shipImage from "../../assets/images/ship.png";

import CargoInput from "../../components/voyage/CargoInput";
import RouteInput from "../../components/voyage/RouteInput";
import DateRangeInput from "../../components/voyage/DateRangeInput";
import VoyageForm from "../../components/voyage/VoyageForm";

import { getRecommendation } from "../../services/api";

const Icon = ({ type }) => {
  const icons = {
    home: "⌂",
    voyage: "➤",
    analysis: "▥",
    vessel: "♜",
    port: "♙",
    simulation: "⟳",
    settings: "⚙",
    search: "⌕",
    bell: "♧",
  };

  return (
    <span className={`icon icon-${type}`}>
      {icons[type]}
    </span>
  );
};

function NewVoyage() {
  const navigate = useNavigate();

  const [cargoType, setCargoType] = useState("Coal");
  const [quantity, setQuantity] = useState("75000");

  const [loadingPort, setLoadingPort] = useState(
    "Hay Point, Australia"
  );

  const [dischargePort, setDischargePort] = useState(
    "Paradip, India"
  );

  const [arrivalDate, setArrivalDate] = useState("");
  const [flexibleDate, setFlexibleDate] = useState(false);

  const [vesselType, setVesselType] = useState(
    "Bulk Carrier"
  );

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
  const [loading, setLoading] = useState(false);

  const handleAnalysis = async () => {
    if (!quantity || Number(quantity) <= 0) {
      setMessage("Please enter a valid cargo quantity.");
      return;
    }

    if (!arrivalDate) {
      setMessage("Please select an arrival date.");
      return;
    }

    const destinationRegion = dischargePort
      .toLowerCase()
      .includes("india")
      ? "East Coast India"
      : dischargePort;

    const recommendationInput = {
      cargo_type: cargoType,
      quantity_tonnes: Number(quantity),
      origin_country: loadingPort
        .split(",")
        .pop()
        .trim(),
      destination_region: destinationRegion,
      arrival_date: arrivalDate,
    };

    setLoading(true);
    setMessage("");

    try {
      const response = await getRecommendation(
        recommendationInput
      );

      sessionStorage.setItem(
        "freightwise_voyage_input",
        JSON.stringify({
          cargoType,
          quantity,
          loadingPort,
          dischargePort,
          arrivalDate,
          flexibleDate,
          vesselType,
          draft,
          loa,
          beam,
          weather,
          contract,
          priority,
          previousVoyage,
          alternativeRoutes,
          whatIf,
        })
      );

      sessionStorage.setItem(
        "freightwise_recommendation",
        JSON.stringify(response)
      );

      navigate("/analysis");
    } catch (error) {
      console.error(
        "FreightWise analysis error:",
        error
      );

      setMessage(
        error.message ||
          "Unable to run FreightWise analysis."
      );
    } finally {
      setLoading(false);
    }
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

      {/* SIDEBAR */}
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

          {/* DASHBOARD */}
          <button
            type="button"
            className="nav-item"
            onClick={() => navigate("/")}
          >
            <Icon type="home" />
            <span>Dashboard</span>
          </button>

          {/* NEW VOYAGE */}
          <button
            type="button"
            className="nav-item active"
            onClick={() => navigate("/new-voyage")}
          >
            <Icon type="voyage" />
            <span>New Voyage</span>
          </button>

          {/* ANALYSIS */}
          <button
            type="button"
            className="nav-item"
            onClick={() => navigate("/analysis")}
          >
            <Icon type="analysis" />
            <span>Analysis</span>
          </button>

          {/* VESSELS */}
          <button
            type="button"
            className="nav-item"
            onClick={() => navigate("/vessels")}
          >
            <Icon type="vessel" />
            <span>Vessels</span>
          </button>

          {/* PORTS */}
          <button
            type="button"
            className="nav-item"
            onClick={() => navigate("/ports")}
          >
            <Icon type="port" />
            <span>Ports</span>
          </button>

          {/* SIMULATION */}
          <button
            type="button"
            className="nav-item"
            onClick={() => navigate("/simulation")}
          >
            <Icon type="simulation" />
            <span>Simulation</span>
          </button>

          {/* SETTINGS */}
          <button
            type="button"
            className="nav-item"
            onClick={() => navigate("/settings")}
          >
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

      {/* MAIN */}
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
              <div className="avatar">
                K
              </div>

              <span>User</span>

              <span className="dropdown-arrow">
                ⌄
              </span>
            </div>

          </div>

        </header>

        {/* HERO */}
        <section className="page-hero">

          <div className="hero-text">
            <h1>Plan a New Voyage</h1>

            <p>
              Provide voyage details to get AI-powered
              recommendations
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

        {/* STEPS */}
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

        {/* COMPONENTS */}
        <section className="content-grid">

          <CargoInput
            cargoType={cargoType}
            setCargoType={setCargoType}
            quantity={quantity}
            setQuantity={setQuantity}
          />

          <RouteInput
            loadingPort={loadingPort}
            setLoadingPort={setLoadingPort}
            dischargePort={dischargePort}
            setDischargePort={setDischargePort}
          />

          <DateRangeInput
            arrivalDate={arrivalDate}
            setArrivalDate={setArrivalDate}
            flexibleDate={flexibleDate}
            setFlexibleDate={setFlexibleDate}
          />

          <VoyageForm
            vesselType={vesselType}
            setVesselType={setVesselType}
            draft={draft}
            setDraft={setDraft}
            loa={loa}
            setLoa={setLoa}
            beam={beam}
            setBeam={setBeam}
            weather={weather}
            setWeather={setWeather}
            contract={contract}
            setContract={setContract}
            priority={priority}
            setPriority={setPriority}
            previousVoyage={previousVoyage}
            setPreviousVoyage={setPreviousVoyage}
            alternativeRoutes={alternativeRoutes}
            setAlternativeRoutes={setAlternativeRoutes}
            whatIf={whatIf}
            setWhatIf={setWhatIf}
          />

        </section>

        {/* BOTTOM ACTIONS */}
        <div className="bottom-actions">

          <button
            type="button"
            className="reset-button"
            onClick={resetForm}
            disabled={loading}
          >
            ⟳
            <span>Reset Form</span>
          </button>

          <button
            type="button"
            className="analysis-button"
            onClick={handleAnalysis}
            disabled={loading}
          >
            <span>
              {loading ? "⏳" : "✨"}
            </span>

            <span>
              {loading
                ? "Running FreightWise Analysis..."
                : "Run FreightWise Analysis"}
            </span>

            <span>→</span>
          </button>

        </div>

        {message && (
          <div className="success-message">
            {message}
          </div>
        )}

      </main>

    </div>
  );
}

export default NewVoyage;