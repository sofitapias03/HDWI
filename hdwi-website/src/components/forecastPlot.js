import React from "react";
import "../styles/Map.css";

function ForecastMap() {
  return (
    <div className="forecast-wrapper">
      <img
        src="http://localhost:5000/map"
        alt="Forecast map"
        className="forecast-image"
      />
    </div>
  );
}

export default Map;