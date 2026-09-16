import React from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function AppLayout({
  page,
  setPage,
  children,
  onSettings,
}) {
  return (
    <div className="fw-shell">
      <Sidebar
        page={page}
        setPage={setPage}
        onSettings={onSettings}
      />

      <section className="fw-content">
        <Header />

        <div className="fw-content-body">
          {children}
        </div>
      </section>
    </div>
  );
}