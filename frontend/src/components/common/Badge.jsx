import React from "react";

export default function Badge({
  children,
  tone = "navy",
  className = "",
}) {
  return (
    <span className={`fw-badge ${tone} ${className}`}>
      {children}
    </span>
  );
}