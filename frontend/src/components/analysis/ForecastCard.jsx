import React, { useState } from "react";

function ForecastChart({ days }) {
  return (
    <div className="forecast-chart">
      <div className="chart-y-axis">
        <span>50</span>
        <span>40</span>
        <span>30</span>
        <span>20</span>
        <span>10</span>
      </div>

      <div className="chart-area">
        <div className="chart-grid">
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>

        <div className="today-line">
          <span>Today</span>
        </div>

        <svg
          className="forecast-svg"
          viewBox="0 0 650 260"
          preserveAspectRatio="none"
        >
          <polyline
            className="historical-line"
            points="
              10,90
              65,70
              120,82
              175,112
              230,108
              285,145
              340,128
              395,132
              450,108
            "
          />

          <polyline
            className="forecast-line"
            points={
              days === 7
                ? "450,108 500,125 550,145 600,160 625,170"
                : days === 30
                ? "450,108 500,115 550,125 600,140 625,150"
                : "450,108 500,122 545,140 590,155 625,170"
            }
          />

          <polyline
            className="confidence-line"
            points={
              days === 7
                ? "450,90 500,105 550,120 600,135 625,145"
                : days === 30
                ? "450,90 500,98 550,108 600,120 625,130"
                : "450,90 500,102 545,115 590,132 625,148"
            }
          />
        </svg>

        <div className="chart-months">
          <span>Jan</span>
          <span>Feb</span>
          <span>Mar</span>
          <span>Apr</span>
          <span>May</span>
          <span>Jun</span>
          <span>Jul</span>
          <span>Aug</span>
          <span>Sep</span>
          <span>Oct</span>
          <span>Nov</span>
          <span>Dec</span>
        </div>
      </div>
    </div>
  );
}

export default function ForecastCard({ data }) {
  const [selectedDays, setSelectedDays] = useState(14);

  const hasForecast =
    data &&
    data.forecast_rate != null &&
    data.data_status !== "UNAVAILABLE";

  const forecastRate = hasForecast
    ? `USD ${Number(data.forecast_rate).toLocaleString()} / day`
    : "Unavailable";

  const confidence =
    data?.confidence != null
      ? `${Math.round(Number(data.confidence) * 100)}%`
      : "Unavailable";

  const currentForecast = {
    change: hasForecast ? forecastRate : "Forecast unavailable",
    description: hasForecast
      ? `Model confidence: ${confidence}`
      : data?.message ||
        "Validated freight forecast is currently unavailable.",
  };



  return (
    <section className="panel forecast-panel">
      <div className="panel-heading">
        <div className="heading-title">
          <span className="heading-icon">▥</span>
          Freight Forecast
        </div>

        <div className="forecast-tabs">
          {[7, 14, 30].map((days) => (
            <button
              key={days}
              className={selectedDays === days ? "selected" : ""}
              onClick={() => setSelectedDays(days)}
              type="button"
            >
              {days} Days
            </button>
          ))}
        </div>
      </div>

      <div className="forecast-content">
        <ForecastChart days={selectedDays} />

        <div className="forecast-insight">
          <span>Forecast Insights</span>

          <strong>{currentForecast.change}</strong>

          <b>Expected decline</b>

          <p>{currentForecast.description}</p>

          <div className="insight-text">
            {hasForecast
              ? `Forecast rate: ${forecastRate}.`
              : "No validated ML forecast is available for this voyage date."}
          </div>
        </div>
      </div>

      <div className="chart-legend">
        <span>
          <i className="legend-dot historical" />
          Historical
        </span>

        <span>
          <i className="legend-dot forecast" />
          Forecast
        </span>

        <span>
          <i className="legend-box" />
          Confidence Range
        </span>
      </div>
    </section>
  );
}