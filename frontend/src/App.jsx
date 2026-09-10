import React from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

/* =========================================================
   PAGES
========================================================= */

import Dashboard from "./pages/Dashboard/Dashboard";

import NewVoyage from "./pages/NewVoyage/NewVoyage";

import Analysis from "./pages/Analysis/Analysis";

import Vessels from "./pages/Vessels/Vessels";

import Ports from "./pages/Ports/Ports";

import Simulation from "./pages/Simulation/Simulation";

import Settings from "./pages/Settings/Settings";

import Profile from "./pages/Profile/Profile";

import Notifications from "./pages/Notifications/Notifications";


/* =========================================================
   APP
========================================================= */

function App() {

  return (

    <BrowserRouter>

      <Routes>


        {/* =================================================
            DASHBOARD
        ================================================= */}

        <Route
          path="/"
          element={<Dashboard />}
        />


        {/* =================================================
            MAIN PAGES
        ================================================= */}

        <Route
          path="/new-voyage"
          element={<NewVoyage />}
        />


        <Route
          path="/analysis"
          element={<Analysis />}
        />


        <Route
          path="/vessels"
          element={<Vessels />}
        />


        <Route
          path="/ports"
          element={<Ports />}
        />


        <Route
          path="/simulation"
          element={<Simulation />}
        />


        <Route
          path="/settings"
          element={<Settings />}
        />


        {/* =================================================
            USER
        ================================================= */}

        <Route
          path="/profile"
          element={<Profile />}
        />


        <Route
          path="/notifications"
          element={<Notifications />}
        />


        {/* =================================================
            FALLBACK
        ================================================= */}

        <Route
          path="*"
          element={
            <Navigate
              to="/"
              replace
            />
          }
        />

      </Routes>

    </BrowserRouter>

  );
}


export default App; 