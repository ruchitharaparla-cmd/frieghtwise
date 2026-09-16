import React from "react";
import { ChevronRight } from "lucide-react";

export default function Field({
  label,
  value = "Select",
  placeholder,
  className = "",
}) {
  return (
    <label className={`fw-field ${className}`}>
      <span>{label}</span>

      <div>
        {value || placeholder}
        <ChevronRight size={13} />
      </div>
    </label>
  );
}