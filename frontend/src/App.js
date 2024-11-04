import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import MonumentPage from './pages/MonumentPage';
import CommunityPage from './pages/CommunityPage';
import AuthProvider from './services/authService';
import Navbar from './components/Navbar';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/monuments" element={<MonumentPage />} />
          <Route path="/community" element={<CommunityPage />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
