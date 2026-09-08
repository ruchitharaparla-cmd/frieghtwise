import React from "react";
import { useNavigate } from "react-router-dom";

import "./RecentVoyages.css";


const RecentVoyages = ({ Icon }) => {

  const navigate = useNavigate();


  const voyages = [
    {
      voyage: "FW-0268",
      cargo: "Coal",
      route: "Hay Point → Paradip",
      status: "Completed",
      statusClass: "completed",
      cost: "₹6.42 Cr",
    },
    {
      voyage: "FW-0267",
      cargo: "Iron Ore",
      route: "Port Hedland → Vizag",
      status: "In Transit",
      statusClass: "transit",
      cost: "₹5.98 Cr",
    },
    {
      voyage: "FW-0266",
      cargo: "Coal",
      route: "Newcastle → Kakinada",
      status: "Loading",
      statusClass: "loading",
      cost: "₹6.21 Cr",
    },
    {
      voyage: "FW-0265",
      cargo: "Fertilizer",
      route: "Muscat → Chennai",
      status: "Completed",
      statusClass: "completed",
      cost: "₹4.87 Cr",
    },
  ];


  return (

    <div className="panel recent-voyages-panel">


      {/* =================================================
          HEADER
          ================================================= */}

      <div className="panel-header">


        <div>

          <h3>

            <Icon
              type="ship"
              size={18}
            />

            Recent Voyages

          </h3>

        </div>


        {/* VIEW ALL */}

        <button
          type="button"
          className="view-all-button"
          onClick={() => navigate("/voyages")}
        >

          View All

          <Icon
            type="arrow"
            size={15}
          />

        </button>


      </div>


      {/* =================================================
          TABLE
          ================================================= */}

      <div className="voyage-table">


        <div className="voyage-table-header">

          <span>
            Voyage
          </span>

          <span>
            Cargo
          </span>

          <span>
            Route
          </span>

          <span>
            Status
          </span>

          <span>
            Cost
          </span>

        </div>


        {/* =================================================
            VOYAGE ROWS
            ================================================= */}

        {voyages.map((voyage) => (

          <div
            className="voyage-table-row"
            key={voyage.voyage}
          >


            <span className="voyage-id">
              {voyage.voyage}
            </span>


            <span>
              {voyage.cargo}
            </span>


            <span className="voyage-route">
              {voyage.route}
            </span>


            <span>

              <span
                className={`voyage-status ${voyage.statusClass}`}
              >

                <span className="status-dot" />

                {voyage.status}

              </span>

            </span>


            <span className="voyage-cost">
              {voyage.cost}
            </span>


          </div>

        ))}


      </div>


    </div>

  );
};


export default RecentVoyages;