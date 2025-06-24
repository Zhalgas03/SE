import React from 'react';
import PhotoSide from '../components/PhotoSide';
import { Outlet } from 'react-router-dom';
import './AuthLayout.css';

function AuthLayout() {
  return (
    <div className="auth-container">
      <div className="photo-side">
        <PhotoSide />
      </div>
      <div className="form-side">
        <Outlet />
      </div>
    </div>
  );
}

export default AuthLayout;
