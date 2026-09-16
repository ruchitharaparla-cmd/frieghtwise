import React from "react";

export default function SectionTitle({
  title,
  right,
  className = "",
}) {
  return (
    <div className={`fw-section-title ${className}`}>
      <h3>{title}</h3>

      {right && (
        typeof right === "string" ? (
          <span>{right}</span>
        ) : (
          right
        )
      )}
    </div>
  );
}