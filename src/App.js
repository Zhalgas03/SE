import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { UserProvider } from './context/UserContext';
import { useUser } from './context/UserContext';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Register from './components/Register';
import AuthLayout from './layouts/AuthLayout';
import HomePage from './pages/HomePage';
import PlannerPage from './pages/PlannerPage';
import GoogleCallback from './components/GoogleCallback';
import TestTripPost from './pages/TestTripPost';

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setUser } = useUser();
  const hideNavbar = ['/login', '/register'].includes(location.pathname);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const username = params.get("username");

    if (token && username) {
      localStorage.setItem("token", token);
      localStorage.setItem("username", username);
      setUser({ username });
      navigate('/');
    }
  }, []);

  return (
    <>
      {!hideNavbar && <Navbar />}
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>
        <Route path="/" element={<HomePage />} />
        <Route path="/planner" element={<PlannerPage />} />
        <Route path="/google/callback" element={<GoogleCallback />} />
        <Route path="/test-trip-post" element={<TestTripPost />} />
      </Routes>
    </>
  );
}

function App() {
  return (
    <UserProvider>
      <Router>
        <AppContent />
      </Router>
    </UserProvider>
  );
}

export default App;
