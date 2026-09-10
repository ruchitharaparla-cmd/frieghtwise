import React from "react";

function DateRangeInput({
  arrivalDate,
  setArrivalDate,
  flexibleDate,
  setFlexibleDate,
}) {
  return (
    <div className="form-card">
      <div className="card-heading">
        <div className="card-icon">▣</div>

        <div>
          <h2>3. Voyage Dates</h2>
          <p>When do you need the vessel?</p>
        </div>
      </div>

      <div className="field">
        <label>
          Expected Arrival Date <span>*</span>
        </label>

        <input
          className="date-input"
          type="date"
          value={arrivalDate}
          onChange={(e) => setArrivalDate(e.target.value)}
        />
      </div>

      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={flexibleDate}
          onChange={(e) => setFlexibleDate(e.target.checked)}
        />

        <span>Flexible date</span>
      </label>

      <div className="info-box">
        <b>ⓘ</b>
        You can select a fixed arrival date or allow flexibility
        for better recommendations.
      </div>
    </div>
  );
}

export default DateRangeInput;