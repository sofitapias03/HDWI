import React from "react";
import "../styles/Map.css";

function Map({ day }) { 
  const handleClick = async (e) => {
    const rect = e.target.getBoundingClientRect();

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const fracX = x / rect.width;
    const fracY = y / rect.height;

    try {
      const res = await fetch("http://localhost:5050/click", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fracX, fracY }),
      });

      const data = await res.json();
      console.log("Click response:", data);
    } catch (err) {
      console.error("Click error:", err);
    }
  };

  return (
    <div className="map-wrapper">
      <img
        src={`https://raw.githubusercontent.com/sofitapias03/HDWI/pulling/maps/maxMap_day_${day}.png`}
        alt="Forecast map"
        className="map-image"
        onClick={handleClick}
      />
    </div>
  );
}

export default Map; 






// import React from "react";
// import "../styles/Map.css";


// function Map({ day = 0 }) {
//   const handleClick = async (e) => {
//     const rect = e.target.getBoundingClientRect();

//     const x = e.clientX - rect.left;
//     const y = e.clientY - rect.top;

//     const fracX = x / rect.width;
//     const fracY = y / rect.height;

//     try {
//       const res = await fetch("http://localhost:5050/click", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ fracX, fracY, day }), // optional: send day too
//       });

//       const data = await res.json();
//       console.log("Click response:", data);
//     } catch (err) {
//       console.error("Click error:", err);
//     }
//   };

//   return (
//     <div className="map-wrapper">
//       <img
//         src={`http://localhost:5050/map?day=${day}&t=${Date.now()}`}
//         alt="Forecast map"
//         className="map-image"
//         onClick={handleClick}
//       />
//     </div>
//   );
// }

// export default Map;





// function Map() {
//   const handleClick = async (e) => {
//     const rect = e.target.getBoundingClientRect();

//     const x = e.clientX - rect.left;
//     const y = e.clientY - rect.top;

//     const fracX = x / rect.width;
//     const fracY = y / rect.height;

//     try {
//       const res = await fetch("http://localhost:5050/click", { 
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ fracX, fracY }),
//       });

//       const data = await res.json();
//       console.log("Click response:", data);
//     } catch (err) {
//       console.error("Click error:", err);
//     }
//   };

//   return (
//     <div className="map-wrapper">
//       <img
//         src="http://localhost:5050/map"
//         alt="Forecast map"
//         className="map-image"
//         onClick={handleClick}
//       />
//     </div>
//   );
// }

// export default Map;