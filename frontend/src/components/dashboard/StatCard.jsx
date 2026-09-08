import React from "react";
import "./StatCard.css";

const StatCard = ({
  Icon,
  iconType,
  iconClass,
  title,
  value,
  subtitle,
  positive = false,
  decoration = "chart",
}) => {
  return (
    <div className="metric-card">

      <div className={`metric-icon ${iconClass}`}>
        <Icon
          type={iconType}
          size={27}
        />
      </div>

      <div className="metric-content">

        <span className="metric-title">
          {title}
        </span>

        <strong>
          {value}
        </strong>

        <span
          className={`metric-subtitle ${
            positive ? "positive" : ""
          }`}
        >
          {subtitle}
        </span>

      </div>

      <div className="metric-decoration">
        <Icon
          type={decoration}
          size={52}
        />
      </div>

    </div>
  );
};

export default StatCard;