import React from "react";
import { Search, Bell, ChevronRight } from "lucide-react";

export default function Header() {
  return (
    <header className="fw-header">
      <div className="fw-search">
        <Search size={15} />
        Search ports, vessels, routes...
      </div>

      <div className="fw-header-right">
        <span>Fri, 12 Sep 2026</span>
        <Bell size={16} />
        <div className="fw-avatar">K</div>
        <span>Keerthi</span>
        <ChevronRight size={14} />
      </div>
    </header>
  );
}
