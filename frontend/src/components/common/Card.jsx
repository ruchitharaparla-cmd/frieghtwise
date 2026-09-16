import React from "react";
import "./Card.css";

function Card({ children, className = "" }) {
  return (
    <section className={`fw-card ${className}`}>
      {children}
    </section>
  );
}

export default Card;