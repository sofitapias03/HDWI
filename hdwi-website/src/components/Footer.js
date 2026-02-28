import React from 'react';
import '../styles/Footer.css'
import EnactusLogo from '../images/EnactusLogo.png'
import ParagonLogo from '../images/ParagonLogo.png'
import HDWILogo from '../images/HDWILogo.png'

function Footer() {
  return (
    <div className = 'footer'>
      <div className = 'info'>
        <p>kya.broderik@ucalgary.ca</p>
        <p>sofia.tapiasmontana@ucalgary.ca</p>
        <p>2500 University Drive NW, Calgary, AB</p>
      </div>

      <div className = 'branding'>
        <p><h2>Student entrepreneurs for social change</h2></p>
        <p>© 2013-{new Date().getFullYear()} Enactus/Paragon University of Calgary.</p>
      </div>

      <div className = 'Logos'>
        <img className = 'logoIcon' src={EnactusLogo} alt='Enactus Logo'/>
        <img className = 'logoIcon' src={HDWILogo} alt='HDWI Logo'/>
        <img className = 'logoIcon' src={ParagonLogo} alt='Paragon Logo'/>
      </div>

    </div>
  );
}

export default Footer;
