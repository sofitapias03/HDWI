import { useState } from 'react'
import "../styles/Map.css";
import fallBackMap from '../images/fall-back-map.png';

function Map({ day }) {
  const runDate = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const [error, setError] = useState(false);

  return (
    <div className="map-wrapper">
      <img
          src={error ? fallBackMap : `https://raw.githubusercontent.com/sofitapias03/HDWI/pulling/maps/maxMap_day_${day}.png?v=${runDate}`}
          alt="Forecast map"
          className="map-image"
          onError={ (e) => {
            e.target.onerror = null;
            setError(true);
          }}
      />
    </div>
  );
}

export default Map; 
