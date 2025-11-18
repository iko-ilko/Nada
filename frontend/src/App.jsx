import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Onboarding from './pages/Onboarding';
import Occupation from './pages/Occupation';
import CameraPermission from './pages/CameraPermission';
import Camera from './pages/Camera';
import PhotoResult from './pages/PhotoResult';
import AnalysisDetail from './pages/AnalysisDetail';
import References from './pages/References';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route path="/occupation" element={<Occupation />} />
        <Route path="/camera-permission" element={<CameraPermission />} />
        <Route path="/camera" element={<Camera />} />
        <Route path="/photo-result" element={<PhotoResult />} />
        <Route path="/analysis-detail" element={<AnalysisDetail />} />
        <Route path="/references" element={<References />} />
      </Routes>
    </Router>
  );
}

export default App;
