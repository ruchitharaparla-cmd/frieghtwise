import React from "react";

export default function Step({
  number,
  title,
  children,
  className = "",
}) {
  return (
    <section className={`fw-step ${className}`}>
      <h3>
        <i>{number}</i>
        {title}
      </h3>

      <div className="fw-field-grid">
        {children}
      </div>
    </section>
  );
}