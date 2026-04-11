import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import Text from '../components/Text';
import '../styles/LandingPage.css';
import '../styles/Map.css';
import MapContainer from '../components/MapContainer'

function Landing() {
  return (
    <div className='landingPage'>
      <Header />

    <div className='island-display'>
      <div className="main-content">
        <div className="map-slider-stack">
          <MapContainer/>
          </div>
        </div>
      <div>
        <Text/>
      </div>
    </div>

      <Footer />
    </div>
  );
}

export default Landing;
