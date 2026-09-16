import React, { useState } from "react";
import "./FreightWiseWidget.css";

import {
  AppLayout,
} from "./components/layout";

import Dashboard from "./pages/Dashboard/Dashboard";
import NewVoyage from "./pages/NewVoyage/NewVoyage";
import Analysis from "./pages/Analysis/Analysis";
import Vessels from "./pages/Vessels/Vessels";
import Ports from "./pages/Ports/Ports";
import Simulation from "./pages/Simulation/Simulation";

export default function FreightWiseWidget() {
  const [page, setPage] = useState("dashboard");

  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return <Dashboard go={setPage} />;

      case "new-voyage":
        return <NewVoyage go={setPage} />;

      case "analysis":
        return <Analysis go={setPage} />;

      case "vessels":
        return <Vessels go={setPage} />;

      case "ports":
        return <Ports go={setPage} />;

      case "simulation":
        return <Simulation go={setPage} />;

      default:
        return <Dashboard go={setPage} />;
    }
  };

  return (
    <AppLayout
      page={page}
      setPage={setPage}
    >
      {renderPage()}
    </AppLayout>
  );
}