import React from "react";
import { ChevronRight } from "lucide-react";

export default function Field({ label, value = "Select", placeholder }) {
  return (
    <label className="fw-field">
      <span>{label}</span>
      <div>
        {value || placeholder}
        <ChevronRight size={13} />
      </div>
    </label>
  );
}