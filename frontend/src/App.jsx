import React, { useEffect, useState } from "react";

import Dashboard from "./pages/Dashboard/Dashboard";
import Vessels from "./pages/Vessels/Vessels";
import "./App.css";

function App() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const handleNavigation = () => {
      setPath(window.location.pathname);
    };

    window.addEventListener("popstate", handleNavigation);

    return () => {
      window.removeEventListener("popstate", handleNavigation);
    };
  }, []);

  if (path === "/vessels") {
    return <Vessels />;
  }

  return <Dashboard />;
}

export default App;