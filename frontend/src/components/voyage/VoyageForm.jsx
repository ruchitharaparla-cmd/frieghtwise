import React from "react";
import portImage from "../../assets/images/port.png";

function VoyageForm({
  vesselType,
  setVesselType,
  draft,
  setDraft,
  loa,
  setLoa,
  beam,
  setBeam,
  weather,
  setWeather,
  contract,
  setContract,
  priority,
  setPriority,
  previousVoyage,
  setPreviousVoyage,
  alternativeRoutes,
  setAlternativeRoutes,
  whatIf,
  setWhatIf,
}) {
  return (
    <>
      {/* CARD 4 - VESSEL REQUIREMENTS */}
      <div className="form-card">
        <div className="card-heading">
          <div className="card-icon">♜</div>

          <div>
            <h2>4. Vessel Requirements</h2>
            <p>Specify your vessel preferences</p>
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label>
              Vessel Type <span>*</span>
            </label>

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
          Enter minimum requirements. We will match the best
          available vessels.
        </div>
      </div>

      {/* CARD 5 - ADDITIONAL CONSTRAINTS */}
      <div className="form-card">
        <div className="card-heading">
          <div className="card-icon">▤</div>

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
                onChange={(e) =>
                  setPreviousVoyage(e.target.checked)
                }
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

      {/* CARD 6 - TIPS */}
      <div className="form-card tips-card">
        <div className="card-heading">
          <div className="bulb-icon">💡</div>

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

        <div
          className="tips-image"
          style={{ backgroundImage: `url(${portImage})` }}
        >
          <div className="tips-quote">
            "Connecting Global Resources
            <br />
            to India's Growth"
          </div>
        </div>
      </div>
    </>
  );
}

export default VoyageForm;