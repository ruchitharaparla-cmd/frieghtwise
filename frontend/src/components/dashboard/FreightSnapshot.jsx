import React from "react";
import "./FreightSnapshot.css";

const FreightChart = () => {
  const historical = [
    [0, 51],
    [7, 45],
    [14, 50],
    [21, 42],
    [28, 47],
    [35, 35],
    [42, 36],
    [49, 32],
    [56, 27],
    [63, 31],
    [70, 28],
    [77, 31],
    [84, 25],
    [91, 34],
  ];

  const forecast = [
    [91, 34],
    [98, 30],
    [105, 27],
    [112, 25],
    [119, 22],
    [126, 20],
    [133, 18],
    [140, 16],
  ];

  const points = (data) =>
    data
      .map(
        ([x, y]) =>
          `${x * 4.45 + 35},${105 - y * 1.55}`
      )
      .join(" ");

  return (
    <div className="freight-chart">

      <svg
        viewBox="0 0 690 135"
        preserveAspectRatio="none"
        className="chart-svg"
      >

        {[20, 40, 60, 80, 100].map((y) => (
          <line
            key={y}
            x1="35"
            x2="660"
            y1={y}
            y2={y}
            className="grid-line"
          />
        ))}

        {[35, 125, 215, 305, 395, 485, 575, 660].map(
          (x) => (
            <line
              key={x}
              x1={x}
              x2={x}
              y1="15"
              y2="105"
              className="grid-line"
            />
          )
        )}

        <path
          d="M440 50 C500 48 550 56 660 64 L660 105 C570 96 500 92 440 70 Z"
          className="confidence-area"
        />

        <polyline
          points={points(historical)}
          className="historical-line"
        />

        <polyline
          points={points(forecast)}
          className="forecast-line"
        />

        {historical.map(([x, y], index) => (
          <circle
            key={`historical-${index}`}
            cx={x * 4.45 + 35}
            cy={105 - y * 1.55}
            r="2.7"
            className="historical-point"
          />
        ))}

        {forecast.map(([x, y], index) => (
          <circle
            key={`forecast-${index}`}
            cx={x * 4.45 + 35}
            cy={105 - y * 1.55}
            r="2.4"
            className="forecast-point"
          />
        ))}

        <line
          x1="440"
          x2="440"
          y1="7"
          y2="108"
          className="today-line"
        />

        <rect
          x="416"
          y="0"
          width="48"
          height="17"
          rx="4"
          className="today-label"
        />

        <text
          x="440"
          y="12"
          textAnchor="middle"
          className="today-text"
        >
          Today
        </text>

        <text
          x="7"
          y="24"
          className="axis-label"
        >
          50
        </text>

        <text
          x="7"
          y="55"
          className="axis-label"
        >
          40
        </text>

        <text
          x="7"
          y="86"
          className="axis-label"
        >
          30
        </text>

        <text
          x="7"
          y="106"
          className="axis-label"
        >
          20
        </text>

      </svg>


      <div className="chart-x-labels">
        <span>Aug 11</span>
        <span>Aug 14</span>
        <span>Aug 17</span>
        <span>Aug 20</span>
        <span>Aug 23</span>
        <span>Aug 26</span>
        <span>Aug 29</span>
        <span>Sep 1</span>
        <span>Sep 4</span>
        <span>Sep 7</span>
      </div>


      <div className="chart-legend">

        <span>
          <i className="legend-line historical-legend" />
          Historical
        </span>

        <span>
          <i className="legend-line forecast-legend" />
          Forecast
        </span>

        <span>
          <i className="legend-area" />
          Confidence Range
        </span>

      </div>

    </div>
  );
};


const FreightSnapshot = ({
  Icon,
  range,
  setRange,
}) => {
  return (
    <div className="panel freight-panel">

      <div className="panel-header">

        <div>

          <h3>
            <Icon
              type="chart"
              size={18}
            />

            Freight Rate Trend
          </h3>

          <span>
            Freight Rate (USD/MT)
          </span>

        </div>


        <div className="range-buttons">

          {["7 Days", "14 Days", "30 Days"].map(
            (item) => (
              <button
                key={item}
                className={
                  range === item
                    ? "selected"
                    : ""
                }
                onClick={() => setRange(item)}
              >
                {item}
              </button>
            )
          )}

        </div>

      </div>


      <div className="chart-container">
        <FreightChart />
      </div>

    </div>
  );
};

export default FreightSnapshot;