import React from "react";

export default function Page({ title, subtitle, children }) {
  return (
    <main className="fw-main">
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