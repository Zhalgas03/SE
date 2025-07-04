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

import AccountPage from './pages/AccountPage';
import LoginSuccess from './pages/LoginSuccess';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import Success from './pages/Success';
import Cancel from './pages/Cancel';
import Favorites from './pages/Favorites';

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setUser } = useUser();
  const hideNavbarRoutes = ['/login', '/register', '/forgot-password', '/reset-password'];
  const hideNavbar = hideNavbarRoutes.includes(location.pathname);


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
  <Route path="/google/callback" element={<GoogleCallback />} />

  <Route path="/account" element={<AccountPage />} />
  <Route path="/login-success" element={<LoginSuccess />} />
  <Route path="/favorites" element={<Favorites />} />
    <Route path="/success" element={<Success />} />
  <Route path="/cancel" element={<Cancel />} />
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
