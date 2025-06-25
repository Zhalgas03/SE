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
import AccountPage from './pages/AccountPage';
import LoginSuccess from './pages/LoginSuccess';

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setUser } = useUser();
  const hideNavbar = ['/login', '/register'].includes(location.pathname);

useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const tokenRaw = params.get("token");
  const username = params.get("username");

  if (tokenRaw && username) {
    try {
      const token = decodeURIComponent(tokenRaw);
      localStorage.setItem("token", token);
      localStorage.setItem("username", username);
      setUser({ username });


      setTimeout(() => {
        navigate('/');
      }, 0);
    } catch (err) {
      console.error("❌ Failed to decode token:", tokenRaw, err);
    }
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
        <Route path="/account" element={<AccountPage />} />
        <Route path="/login-success" element={<LoginSuccess />} />
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
