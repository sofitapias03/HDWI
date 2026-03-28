import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import Map from '../components/Map';
import SliderDays from '../components/SliderDays';
import Graph from '../components/Graph';
import '../styles/LandingPage.css';
import '../styles/Map.css';

function Landing() {
  return (
    <div className='landingPage'>
      <Header />

      <div className="main-content">
        <div className="map-slider-stack">
          <Map />
          <SliderDays />
        </div>
        <div className="graph-wrapper">
          <Graph />
        </div>
      </div>

      <Footer />
    </div>
  );
}

export default Landing;
