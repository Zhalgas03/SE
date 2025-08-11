// src/pages/LoginSuccess.js
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

function LoginSuccess() {
  const { setUser } = useUser();
  const navigate = useNavigate();

useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const token = decodeURIComponent(params.get("token"));
  const username = params.get("username");

  if (token && username) {
    localStorage.setItem("token", token);
    localStorage.setItem("username", username);
    setUser({ username }, token);
    setTimeout(() => {
      navigate('/', { replace: true });
    }, 100);
  }
}, []);

  return (
    <div className="d-flex vh-100 justify-content-center align-items-center">
      <div>Logging you in...</div>
    </div>
  );
}

export default LoginSuccess;