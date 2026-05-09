
import Slider from "rc-slider";
import "rc-slider/assets/index.css";
import "../styles/Slider.css";

export default function SliderDays({selectedDay, setSelectedDay}) {
  const days = 7;

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
    "#FFD4A3",
    "#FFB8CE",
    "#FF80A8",
    "#CC8AD0",
    "#BE6BC4",
    "#A486A7",
    "#8C6990",
  ];

  return (
    <div className="slider-wrapper" data-testid="day-slider">
      <Slider
        min={0}
        max={days - 1}
        step={1}
        value={selectedDay}
        onChange={setSelectedDay}
        trackStyle={{
          backgroundColor: colors[selectedDay],
          height: 20,
          borderRadius: 18,
        }}
        railStyle={{ height: 20, borderRadius: 18 }}
        handleStyle={{
          backgroundColor: "black",
          borderColor: "black",
          height: 30,
          width: 30,
          marginTop: -5,
          opacity: 1,           
          boxShadow: "none" ,
        }}
       
        tipFormatter={(val) => (val === 0 ? "Today" : dates[val])} // <-- updated
        tipProps={{ visible: true, placement: "top" }}
      />
    </div>
  );
}
