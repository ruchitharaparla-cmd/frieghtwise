import React from "react";

export default function PageContainer({
  title,
  subtitle,
  children,
  className = "",
}) {
  return (
    <main className={`fw-main ${className}`}>
      <div className="fw-page-title">
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>

        <span>MARITIME INTELLIGENCE</span>
      </div>

      {children}
    </main>
  );
}