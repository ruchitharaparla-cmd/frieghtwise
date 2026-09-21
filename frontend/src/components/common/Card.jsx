import React from "react";

export default function Card({ children, className = "" }) {
  return <section className={`fw-card ${className}`}>{children}</section>;
}
