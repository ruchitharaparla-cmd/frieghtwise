import React, { useState } from "react";
import { Play, RotateCcw } from "lucide-react";

import Card from "../../components/common/Card";
import Field from "../../components/common/Field";
import SectionTitle from "../../components/common/SectionTitle";
import PageContainer from "../../components/common/PageContainer";

export default function Simulation() {
  const [vessel, setVessel] = useState("Capesize");
  const [cargo, setCargo] = useState("75000");
  const [fuelPrice, setFuelPrice] = useState("650");
  const [portWaiting, setPortWaiting] = useState("18");
  const [result, setResult] = useState(null);

  const runSimulation = () => {
    const cargoValue = Number(cargo) || 0;
    const fuelValue = Number(fuelPrice) || 0;
    const waitingValue = Number(portWaiting) || 0;

    const vesselFactor =
      vessel === "Capesize" ? 1.18 : vessel === "Panamax" ? 1.05 : 0.92;

    const baseFreight = cargoValue * 16.6 * vesselFactor;
    const fuelCost = fuelValue * 320;
    const waitingCost = waitingValue * 8500;
    const totalCost = baseFreight + fuelCost + waitingCost;

    setResult({
      baseFreight,
      fuelCost,
      waitingCost,
      totalCost,
    });
  };

  const resetSimulation = () => {
    setVessel("Capesize");
    setCargo("75000");
    setFuelPrice("650");
    setPortWaiting("18");
    setResult(null);
  };

  return (
    <PageContainer
      title="Simulation"
      subtitle="Compare voyage scenarios by adjusting operational and cost assumptions."
    >
      <div className="fw-two-column-grid">
        <Card>
          <SectionTitle title="Simulation inputs" />

          <Field label="Vessel class" value={vessel} />

          <div className="fw-form-field">
            <label htmlFor="simulation-vessel">Select vessel class</label>

            <select
              id="simulation-vessel"
              value={vessel}
              onChange={(event) => setVessel(event.target.value)}
            >
              <option value="Capesize">Capesize</option>
              <option value="Panamax">Panamax</option>
              <option value="Supramax">Supramax</option>
            </select>
          </div>

          <div className="fw-form-field">
            <label htmlFor="simulation-cargo">
              Cargo quantity (MT)
            </label>

            <input
              id="simulation-cargo"
              type="number"
              value={cargo}
              onChange={(event) => setCargo(event.target.value)}
            />
          </div>

          <div className="fw-form-field">
            <label htmlFor="simulation-fuel">
              Fuel price (USD/MT)
            </label>

            <input
              id="simulation-fuel"
              type="number"
              value={fuelPrice}
              onChange={(event) => setFuelPrice(event.target.value)}
            />
          </div>

          <div className="fw-form-field">
            <label htmlFor="simulation-waiting">
              Port waiting time (hours)
            </label>

            <input
              id="simulation-waiting"
              type="number"
              value={portWaiting}
              onChange={(event) => setPortWaiting(event.target.value)}
            />
          </div>

          <div className="fw-actions">
            <button
              type="button"
              className="fw-primary"
              onClick={runSimulation}
            >
              <Play size={16} />
              Run simulation
            </button>

            <button
              type="button"
              className="fw-secondary"
              onClick={resetSimulation}
            >
              <RotateCcw size={16} />
              Reset
            </button>
          </div>
        </Card>

        <Card>
          <SectionTitle title="Simulation result" />

          {!result ? (
            <div className="fw-empty-state">
              Adjust the inputs and run the simulation to view estimated
              voyage costs.
            </div>
          ) : (
            <div className="fw-simulation-result">
              <div className="fw-simulation-total">
                <span>Estimated total cost</span>
                <strong>
                  $
                  {result.totalCost.toLocaleString("en-US", {
                    maximumFractionDigits: 0,
                  })}
                </strong>
              </div>

              <div className="fw-simulation-breakdown">
                <div>
                  <span>Base freight</span>
                  <strong>
                    $
                    {result.baseFreight.toLocaleString("en-US", {
                      maximumFractionDigits: 0,
                    })}
                  </strong>
                </div>

                <div>
                  <span>Fuel cost</span>
                  <strong>
                    $
                    {result.fuelCost.toLocaleString("en-US", {
                      maximumFractionDigits: 0,
                    })}
                  </strong>
                </div>

                <div>
                  <span>Port waiting cost</span>
                  <strong>
                    $
                    {result.waitingCost.toLocaleString("en-US", {
                      maximumFractionDigits: 0,
                    })}
                  </strong>
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>
    </PageContainer>
  );
}