import React from "react";

export default function SectionTitle({ title, right }) {
  return (
    <div className="fw-section-title">
      <h3>{title}</h3>
      {right}
    </div>
  );
}