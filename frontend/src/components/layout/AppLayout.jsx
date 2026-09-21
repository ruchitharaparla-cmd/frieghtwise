import React from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function AppLayout({ page, setPage, children }) {
  return (
    <div className="fw-shell">
      <Sidebar page={page} setPage={setPage} />
      <div className="fw-content">
        <Header />
        {children}
      </div>
    </div>
  );
}