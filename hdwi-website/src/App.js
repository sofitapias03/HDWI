// import React from 'react';
// import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// import Landing from './pages/Landing';

// function App() {
//   return (
//     <Router>
//       <Routes>
//         <Route path="/" element={<Landing />} />
//       </Routes>
//     </Router>
//   );
// }

// export default App;

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';

function App() {
  return (
    <Router basename="/HDWI">
      <Routes>
        <Route path="/" element={<Landing />} />
      </Routes>
    </Router>
  );
}

export default App;