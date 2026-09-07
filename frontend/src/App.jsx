import React, { useEffect, useState } from "react";

import Dashboard from "./pages/Dashboard/Dashboard";
import Vessels from "./pages/Vessels/Vessels";
import Login from "./pages/Login/Login";
import Settings from "./pages/Settings/Settings";
import NotFound from "./pages/NotFound/NotFound";

import "./App.css";


function App() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setPath(window.location.pathname);
    };

    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);


  if (path === "/login") {
    return <Login />;
  }


  if (path === "/vessels") {
    return <Vessels />;
  }


  if (path === "/settings") {
    return <Settings />;
  }


  if (path === "/") {
    return <Dashboard />;
  }


  return <NotFound />;
}


export default App;