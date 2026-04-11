import { useState } from "react";
import Map from "./Map";
import SliderDays from "./SliderDays";

function MapContainer() {
  const [day, setDay] = useState(0);

  return (
    <>
      <Map day={day} />
      <SliderDays selectedDay={day} setSelectedDay={setDay} />
      
    </>
  );
}

export default MapContainer;