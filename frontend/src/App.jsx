import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard/Dashboard";
import NewVoyage from "./pages/NewVoyage/NewVoyage";
import Analysis from "./pages/Analysis/Analysis";
import Vessels from "./pages/Vessels/Vessels";
import Ports from "./pages/Ports/Ports";
import Simulation from "./pages/Simulation/Simulation";
import Settings from "./pages/Settings/Settings";
import Profile from "./pages/Profile/Profile";
import Notifications from "./pages/Notifications/Notifications";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new-voyage" element={<NewVoyage />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/vessels" element={<Vessels />} />
        <Route path="/ports" element={<Ports />} />
        <Route path="/simulation" element={<Simulation />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/notifications" element={<Notifications />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;