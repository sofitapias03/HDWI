import { useState, useEffect } from "react";

const DEFAULT_LAT = 0;
const DEFAULT_LON = 0;

export default function Graph({ lat = DEFAULT_LAT, lon = DEFAULT_LON }) {
  const [imgSrc, setImgSrc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetch(`http://localhost:5001/forecast?lat=${lat}&lon=${lon}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        return res.blob();
      })
      .then((blob) => {
        setImgSrc(URL.createObjectURL(blob));
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [lat, lon]);

  return (
    <div style={styles.wrapper}>

        {imgSrc && !loading && (
          <img src={imgSrc} alt="HDWI Forecast Plot" style={styles.img} />
        )}
    </div>
  );
}

const styles = {
  wrapper: {
    fontFamily: "'Courier New', monospace",
    background: "#0d1117",
    border: "1px solid #30363d",
    borderRadius: "6px",
    overflow: "hidden",
    width: "100%",
    maxWidth: "100%", 

  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 16px",
    background: "#161b22",
    borderBottom: "1px solid #30363d",
  },
  label: {
    color: "#e6edf3",
    fontWeight: "bold",
    fontSize: "13px",
    letterSpacing: "0.05em",
    textTransform: "uppercase",
  },
  coords: {
    color: "#8b949e",
    fontSize: "12px",
  },
  body: {
    minHeight: "200px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "8px",
  },
  center: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "12px",
  },
  spinner: {
    width: "32px",
    height: "32px",
    border: "3px solid #30363d",
    borderTop: "3px solid #58a6ff",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  statusText: {
    color: "#8b949e",
    fontSize: "13px",
    margin: 0,
  },
  errorText: {
    color: "#f85149",
    fontSize: "13px",
    margin: 0,
  },
  img: {
    width: "100%",
    height: "auto",
    display: "block",
    borderRadius: "4px",
  },
};
