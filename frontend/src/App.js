import React, { useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
  useNavigate
} from 'react-router-dom';

import { UserProvider } from './context/UserContext';
import { useUser } from './context/UserContext';
import { TripProvider } from './context/TripContext';

import Navbar from './components/Navbar';
import Login from './components/Login';
import Register from './components/Register';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';

import HomePage from './pages/HomePage';
import PlannerPage from './pages/PlannerPage';
import AccountPage from './pages/AccountPage';
import LoginSuccess from './pages/LoginSuccess';
import Favorites from './pages/Favorites';
import Success from './pages/Success';
import Cancel from './pages/Cancel';
import GuestVotePage from './pages/GuestVotePage';

import AuthLayout from './layouts/AuthLayout';

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setUser } = useUser();

  const hideNavbarRoutes = ['/login', '/register', '/forgot-password', '/reset-password'];
  const hideNavbar = hideNavbarRoutes.includes(location.pathname);

  // 🔐 Проверка авторизации
  useEffect(() => {
    const token = localStorage.getItem("token");

    const publicRoutes = [
      '/',
      '/login',
      '/register',
      '/forgot-password',
      '/reset-password',
      '/google/callback',
      '/vote'
    ];

    const isPublic = publicRoutes.some(path =>
      location.pathname === path || location.pathname.startsWith(path + '/')
    );

    if (!token && !isPublic) {
      navigate('/login');
    }
  }, [location.pathname, navigate]);

  return (
    <>
      {!hideNavbar && <Navbar />}
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
        </Route>

        <Route path="/" element={<HomePage />} />
        <Route path="/planner" element={<PlannerPage />} />
        <Route path="/account" element={<AccountPage />} />
        <Route path="/login-success" element={<LoginSuccess />} />
        <Route path="/favorites" element={<Favorites />} />
        <Route path="/success" element={<Success />} />
        <Route path="/cancel" element={<Cancel />} />
        <Route path="/vote/:tripId" element={<GuestVotePage />} />
      </Routes>
    </>
  );
}

function App() {
  return (
    <UserProvider>
      <TripProvider>
        <Router>
          <AppContent />
        </Router>
      </TripProvider>
    </UserProvider>
  );
}

export default App;
