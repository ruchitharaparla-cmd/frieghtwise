import React from "react";

function PortCard({ icon: Icon, title, value, type = "" }) {
  return (
    <div className="ports-summary-card">
      <div className={`ports-summary-icon ${type}`}>
        <Icon size={23} />
      </div>

      <div>
        <span>{title}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

export default PortCard;