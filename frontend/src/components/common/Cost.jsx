import React from "react";

export default function Cost({ label, value, strong }) {
  return (
    <div className={`fw-cost ${strong ? "strong" : ""}`}>
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

