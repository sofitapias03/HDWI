import { useState } from "react";
import Slider from "rc-slider";
import "rc-slider/assets/index.css";
import "../styles/Slider.css";

export default function SliderDays() {
  const days = 7;
  const [selectedDay, setSelectedDay] = useState(0);

  const getNextDates = (days) => {
    const dates = [];
    const today = new Date();
    for (let i = 0; i < days; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push(date.toLocaleDateString("en-CA"));
    }
    return dates;
  };

  const dates = getNextDates(days);

  const colors = [
    "#8C6990",
    "#A486A7",
    "#BE6BC4",
    "#CC8AD0",
    "#FF80A8",
    "#FFB8CE",
    "#FFD4A3",
  ];

  return (
    <div className="slider-wrapper">
      <Slider
        min={0}
        max={days - 1}
        step={1}
        value={selectedDay}
        onChange={setSelectedDay}
        trackStyle={{
          backgroundColor: colors[selectedDay],
          height: 20,
          borderRadius: 10,
        }}
        railStyle={{ height: 20, borderRadius: 10 }}
        handleStyle={{
          backgroundColor: "#fff",
          borderColor: "#000",
          height: 25,
          width: 25,
          marginTop: -2.5,
        }}
        dotStyle={{ display: "none" }}
        tipFormatter={(val) => (val === 0 ? "Today" : dates[val])} // <-- updated
        tipProps={{ visible: true, placement: "top" }}
      />
    </div>
  );
}
