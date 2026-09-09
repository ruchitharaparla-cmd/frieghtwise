import React from "react";
import {
  CheckCircle2,
  Navigation,
  XCircle,
} from "lucide-react";

import "./CompatibilityBadge.css";

export function FitBadge({ value }) {
  const className =
    value === "Excellent"
      ? "fit-excellent"
      : value === "Good"
        ? "fit-good"
        : "fit-moderate";

  return (
    <span className={`fit-badge ${className}`}>
      <CheckCircle2 size={12} />
      {value}
    </span>
  );
}

export function AvailabilityBadge({ value }) {
  let icon = <CheckCircle2 size={12} />;
  let className = "availability-available";

  if (value === "In Positioning") {
    icon = <Navigation size={12} />;
    className = "availability-positioning";
  }

  if (value === "Unavailable") {
    icon = <XCircle size={12} />;
    className = "availability-unavailable";
  }

  return (
    <span className={`availability-badge ${className}`}>
      {icon}
      {value}
    </span>
  );
}