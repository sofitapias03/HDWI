import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import Map from '../components/Map';
import '../styles/LandingPage.css';

function Landing() {
  return (
    <div className = 'landingPage'>
      <Header />
      <Map />
      <Footer />
    </div>
  );
}

export default Landing;
