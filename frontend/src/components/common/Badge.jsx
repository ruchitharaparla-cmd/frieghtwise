import React from "react";

export default function Badge({ children, tone = "navy" }) {
  return <span className={`fw-badge ${tone}`}>{children}</span>;
}
