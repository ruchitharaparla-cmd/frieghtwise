import React from "react";
import {
  CheckCircle2,
  Star,
  ArrowRight,
} from "lucide-react";

import {
  FitBadge,
  AvailabilityBadge,
} from "./CompatibilityBadge";

import "./VesselCard.css";

export default function VesselCard({
  vessel,
  onViewDetails,
}) {
  return (
    <article
      className={`vessel-card ${
        vessel.recommended ? "recommended-card" : ""
      }`}
    >
      <div className="vessel-card-image">
        <img
          src={vessel.image}
          alt={`${vessel.name} bulk carrier`}
        />

        {vessel.recommended && (
          <div className="ai-recommended">
            <CheckCircle2 size={13} />
            AI Recommended
          </div>
        )}

        {vessel.recommended && (
          <button
            className="favorite-button"
            aria-label="Favorite vessel"
          >
            <Star
              size={18}
              fill="currentColor"
            />
          </button>
        )}
      </div>

      <div className="vessel-card-body">

        <div className="vessel-card-title">
          <h3>{vessel.name}</h3>

          <p>
            {vessel.dwt.toLocaleString()} DWT
            <span>|</span>
            {vessel.type}
          </p>
        </div>

        <div className="vessel-card-details">

          <div className="fit-section">

            <div className="fit-row">
              <span>Cargo Fit</span>

              <FitBadge
                value={vessel.cargoFit}
              />
            </div>

            <div className="fit-row">
              <span>Port Fit</span>

              <FitBadge
                value={vessel.portFit}
              />
            </div>

            <div className="fit-row">
              <span>Availability</span>

              <AvailabilityBadge
                value={vessel.availability}
              />
            </div>

          </div>

          <div className="estimated-cost">

            <span>Est. Cost</span>

            <strong>
              {typeof vessel.cost === "number" ? `₹ ${vessel.cost.toFixed(2)} Cr` : "Unavailable"}
            </strong>

            <small>
              {typeof vessel.costPerMt === "number" ? `($${vessel.costPerMt.toFixed(1)} / MT)` : "(N/A)"}
            </small>

          </div>

        </div>

        <button
          className="view-details-link"
          onClick={() => onViewDetails(vessel)}
        >
          View Details
          <ArrowRight size={15} />
        </button>

      </div>
    </article>
  );
}