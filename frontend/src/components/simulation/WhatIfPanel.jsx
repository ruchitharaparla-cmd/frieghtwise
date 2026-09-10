import React, { useState } from "react";
import {
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Clock3,
  MapPin,
  Play,
  Settings,
  Ship,
  Sparkles,
} from "lucide-react";

import "./WhatIfPanel.css";
import simulImage from "../../assets/images/simul.png";

export default function WhatIfPanel() {
  const [charteringDate, setCharteringDate] = useState("2026-09-12");
  const [waitingPeriod, setWaitingPeriod] = useState("7");
  const [vessel, setVessel] = useState("MV Ocean Star");
  const [route, setRoute] = useState("Hay Point → Paradip");
  const [running, setRunning] = useState(false);
  const [completed, setCompleted] = useState(true);

  const runSimulation = () => {
    setRunning(true);
    setCompleted(false);

    setTimeout(() => {
      setRunning(false);
      setCompleted(true);
    }, 800);
  };

  return (
    <>
      {/* HERO */}
      <section className="simulation-hero">
        <div className="simulation-hero-content">
          <span className="hero-eyebrow">
            FREIGHTWISE SIMULATION ENGINE
          </span>

          <h1>What-If Analysis</h1>

          <p>
            Compare different chartering windows and scenarios
          </p>
        </div>

        <img
          src={simulImage}
          alt="Cargo ship at port"
          className="simulation-hero-ship"
        />

        <div className="simulation-hero-slogan">
          <strong>Simulate Today.</strong>
          <strong>Sail Smarter</strong>
          <strong>Tomorrow.</strong>
          <span />
        </div>
      </section>

      {/* PARAMETERS */}
      <section className="parameters-card">
        <div className="parameters-heading">
          <div className="parameters-icon">
            <Settings size={27} />
          </div>

          <div>
            <h2>Simulation Parameters</h2>

            <p>
              Adjust the inputs to compare different scenarios
            </p>
          </div>
        </div>

        <div className="parameter-grid">
          {/* DATE */}
          <div className="parameter-field">
            <label>Chartering Date</label>

            <div className="input-wrapper">
              <CalendarDays size={19} />

              <input
                type="date"
                value={charteringDate}
                onChange={(e) =>
                  setCharteringDate(e.target.value)
                }
              />
            </div>
          </div>

          {/* WAITING PERIOD */}
          <div className="parameter-field">
            <label>Waiting Period</label>

            <div className="select-wrapper">
              <Clock3 size={19} />

              <select
                value={waitingPeriod}
                onChange={(e) =>
                  setWaitingPeriod(e.target.value)
                }
              >
                <option value="0">Charter Now</option>
                <option value="7">Wait 7 Days</option>
                <option value="14">Wait 14 Days</option>
                <option value="21">Wait 21 Days</option>
              </select>

              <ChevronDown
                size={18}
                className="select-arrow"
              />
            </div>
          </div>

          {/* VESSEL */}
          <div className="parameter-field">
            <label>Vessel Option</label>

            <div className="select-wrapper">
              <Ship size={19} />

              <select
                value={vessel}
                onChange={(e) => setVessel(e.target.value)}
              >
                <option>MV Ocean Star</option>
                <option>MV Pacific Trader</option>
                <option>MV Eastern Horizon</option>
                <option>MV Sea Falcon</option>
              </select>

              <ChevronDown
                size={18}
                className="select-arrow"
              />
            </div>
          </div>

          {/* ROUTE */}
          <div className="parameter-field">
            <label>Route / Port Option</label>

            <div className="select-wrapper">
              <MapPin size={19} />

              <select
                value={route}
                onChange={(e) => setRoute(e.target.value)}
              >
                <option>Hay Point → Paradip</option>
                <option>Newcastle → Paradip</option>
                <option>Gladstone → Visakhapatnam</option>
                <option>Hay Point → Visakhapatnam</option>
              </select>

              <ChevronDown
                size={18}
                className="select-arrow"
              />
            </div>
          </div>

          {/* RUN */}
          <button
            className="run-simulation-button"
            onClick={runSimulation}
            disabled={running}
          >
            <Play size={20} fill="currentColor" />

            <span>
              {running ? "Running..." : "Run Simulation"}
            </span>
          </button>
        </div>

        {/* STATUS */}
        <div
          className={`simulation-status ${
            completed
              ? "status-success"
              : "status-running"
          }`}
        >
          {completed ? (
            <>
              <CheckCircle2 size={19} />

              <span>
                Simulation completed using the selected parameters.
              </span>
            </>
          ) : (
            <>
              <Sparkles size={19} />

              <span>
                Running simulation with the selected parameters...
              </span>
            </>
          )}
        </div>
      </section>
    </>
  );
}