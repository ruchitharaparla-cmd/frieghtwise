import React from "react";

export default function Metric({ label, value, sub }) {
  return (
    <div className="fw-metric">
      <span>{label}</span>
      <b>{value}</b>
      {sub && <small>{sub}</small>}
    </div>
  );
}
