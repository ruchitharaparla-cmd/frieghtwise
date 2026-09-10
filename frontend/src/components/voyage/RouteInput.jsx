import React from "react";

function RouteInput({
  loadingPort,
  setLoadingPort,
  dischargePort,
  setDischargePort,
}) {
  const swapPorts = () => {
    const currentLoading = loadingPort;
    setLoadingPort(dischargePort);
    setDischargePort(currentLoading);
  };

  return (
    <div className="form-card">
      <div className="card-heading">
        <div className="card-icon">⌖</div>

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

        <button
          type="button"
          className="swap-button"
          onClick={swapPorts}
        >
          ⇄
        </button>

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
          <strong>
            Distance (approx.): 5,620 nautical miles
          </strong>
          <br />
          Estimated voyage duration: 24 – 28 days
        </div>
      </div>
    </div>
  );
}

export default RouteInput;