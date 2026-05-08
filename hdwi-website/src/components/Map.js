import { useState } from 'react'
import "../styles/Map.css";
import fallBackMap from '../images/fall-back-map.png';

function Map({ day }) {
  const runDate = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const [imgSrc, setImgSrc] = useState (
    `https://raw.githubusercontent.com/sofitapias03/HDWI/pulling/maps/maxMap_day_${day}.png?v=${runDate}`
  );

  return (
    <div className="map-wrapper">
      <img
          src={imgSrc}
          alt="Forecast map"
          className="map-image"
          onError={ (e) => {
            e.target.onerror = null;
            setImgSrc(fallBackMap)
          }}
      />
    </div>
  );
}

export default Map; 
