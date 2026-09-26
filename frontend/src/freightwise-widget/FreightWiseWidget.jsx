import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout";
import Dashboard from "../pages/Dashboard/Dashboard";
import NewVoyage from "../pages/NewVoyage/NewVoyage";
import Analysis from "../pages/Analysis/Analysis";
import Vessels from "../pages/Vessels/Vessels";
import Ports from "../pages/Ports/Ports";
import Simulation from "../pages/Simulation/Simulation";
import "./FreightWiseWidget.css";

function pageFromPath(pathname) {
  const value = pathname.replace(/^\//, "");
  return ["dashboard", "new-voyage", "analysis", "vessels", "ports", "simulation"].includes(value)
    ? value
    : "dashboard";
}

export default function FreightWiseWidget() {
  const location = useLocation();
  const [page, setPage] = useState(() => pageFromPath(window.location.pathname));
  const [recommendation, setRecommendation] = useState(null);

  useEffect(() => {
    const requested = pageFromPath(location.pathname);
    setPage(requested);

  }, [location.pathname]);

  const renderPage = () => {
    switch (page) {
      case "new-voyage":
  return (
    <NewVoyage
      go={setPage}
      setRecommendation={setRecommendation}
    />
  );
      case "analysis":
  return (
    <Analysis
      go={setPage}
      recommendation={recommendation}
    />
  );
      case "vessels":
        return <Vessels go={setPage} />;      case "ports":
        return <Ports go={setPage} />;
      case "simulation":
        return <Simulation go={setPage} />;
      default:
        return <Dashboard go={setPage} />;
    }
  };

  return (
    <AppLayout page={page} setPage={setPage}>
      {renderPage()}
    </AppLayout>
  );
}
