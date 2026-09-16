import React from "react";

export default function Metric({
  label,
  value,
  sub,
  className = "",
}) {
  return (
    <div className={`fw-metric ${className}`}>
      <span>{label}</span>

      <b>{value}</b>

      {sub && (
        <small>{sub}</small>
      )}
    </div>
  );
}