import React, { useEffect, useState } from 'react';
import { useLocation, Outlet } from 'react-router-dom';
import PhotoSide from '../components/PhotoSide';
import './AuthLayout.css';

function AuthLayout() {
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    handleResize(); // Initial check
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isForgotOrReset = ['/forgot-password', '/reset-password'].includes(location.pathname);

  // ✅ Mobile version — no animation, no PhotoSide
  if (isMobile) {
    return (
      <div className="auth-mobile-wrapper">
        <div className="form-side full-width">
          <Outlet />
        </div>
      </div>
    );
  }

  // ✅ Desktop version — with slider & photo sides
  return (
    <div className="auth-slider-container">
      <div className={`auth-slider-wrapper ${isForgotOrReset ? 'reverse' : ''}`}>
        {/* Slide 1: Login/Register */}
        <div className="auth-slide">
          <div className="photo-side">
            <PhotoSide />
          </div>
          <div className="form-side">
            {['/login', '/register'].includes(location.pathname) && <Outlet />}
          </div>
        </div>

        {/* Slide 2: Forgot/Reset */}
        <div className="auth-slide">
          <div className="form-side">
            {isForgotOrReset && <Outlet />}
          </div>
          <div className="photo-side">
            <PhotoSide />
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthLayout;
