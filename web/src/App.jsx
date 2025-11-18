import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Onboarding from './pages/Onboarding';
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
        <Route path="/camera-permission" element={<CameraPermission />} />
        <Route path="/camera" element={<Camera />} />
        <Route path="/photo-result" element={<PhotoResult />} />
        <Route path="/analysis-detail" element={<AnalysisDetail />} />
        <Route path="/references" element={<References />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
