import React from "react";

function CargoInput({
  cargoType,
  setCargoType,
  quantity,
  setQuantity,
}) {
  return (
    <div className="form-card">
      <div className="card-heading">
        <div className="card-icon">▣</div>

        <div>
          <h2>1. Cargo Details</h2>
          <p>Tell us what you want to ship</p>
        </div>
      </div>

      <div className="form-row">
        <div className="field">
          <label>
            Cargo Type <span>*</span>
          </label>

          <select
            value={cargoType}
            onChange={(e) => setCargoType(e.target.value)}
          >
            <option>Coal</option>
            <option>Iron Ore</option>
            <option>Fertilizer</option>
            <option>Grain</option>
            <option>Other Bulk Cargo</option>
          </select>
        </div>

        <div className="field">
          <label>
            Quantity (MT) <span>*</span>
          </label>

          <div className="input-unit">
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
            <span>MT</span>
          </div>
        </div>
      </div>

      <div className="info-box">
        <b>ⓘ</b>
        Supported: Coal, Iron Ore, Fertilizer, Grain and other bulk
        cargoes.
      </div>
    </div>
  );
}

export default CargoInput;