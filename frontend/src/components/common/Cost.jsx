import React from "react";

export default function Cost({
  label,
  value,
  strong = false,
  className = "",
}) {
  return (
    <div className={`fw-cost ${strong ? "strong" : ""} ${className}`}>
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}