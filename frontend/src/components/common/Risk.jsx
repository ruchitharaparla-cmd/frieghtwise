import React from "react";
import Badge from "./Badge";

export default function Risk({
  label,
  value,
  tone = "teal",
  className = "",
}) {
  return (
    <div className={`fw-risk ${className}`}>
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
    </div>
  );
}