import React from 'react';
import PhotoSide from '../components/PhotoSide';
import { Outlet } from 'react-router-dom';

function AuthLayout() {
  return (
    <div style={{ margin: 0, padding: 0 }}>
      <div className="row g-0" style={{ margin: 0, padding: 0 }}>
        <PhotoSide />
        <div className="col-md-6 d-flex align-items-center justify-content-center p-0">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

export default AuthLayout;
