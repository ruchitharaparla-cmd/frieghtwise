import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import FreightWiseWidget from "./freightwise-widget/FreightWiseWidget";
import Dashboard from "./pages/Dashboard/Dashboard";
import Login from "./pages/Login/Login";
import Register from "./pages/Register/Register";
import Settings from "./pages/Settings/Settings";
import Profile from "./pages/Profile/Profile";
import Notifications from "./pages/Notifications/Notifications";
import NotFound from "./pages/NotFound/NotFound";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<FreightWiseWidget />} />
        <Route path="/dashboard" element={<FreightWiseWidget />} />
        <Route path="/new-voyage" element={<FreightWiseWidget />} />
        <Route path="/analysis" element={<FreightWiseWidget />} />
        <Route path="/vessels" element={<FreightWiseWidget />} />
        <Route path="/ports" element={<FreightWiseWidget />} />
        <Route path="/simulation" element={<FreightWiseWidget />} />

        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/notifications" element={<Notifications />} />

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}