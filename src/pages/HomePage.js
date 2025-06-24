import React, { useEffect, useState } from 'react';
import { useUser } from '../context/UserContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthRedirect } from '../hooks/useAuthRedirect';

function HomePage() {
  const { setUser } = useUser();
  const navigate = useNavigate();
  const location = useLocation();
  const { goToPlanner } = useAuthRedirect();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    handleResize(); // check on mount
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get('token');
    const username = params.get('username');

    if (token && username) {
      setUser({ token, username });
      localStorage.setItem('token', token);
      localStorage.setItem('username', username);
      navigate('/', { replace: true });
    }
  }, [location, navigate, setUser]);

  const username = localStorage.getItem('username');

  const mobileCards = [
    { icon: 'bi-airplane-engines', text: 'Pick destination' },
    { icon: 'bi-globe2', text: 'AI step-by-step' },
    { icon: 'bi-journal-check', text: 'Get itinerary' },
  ];

  const desktopCards = [
    { icon: 'bi-airplane-engines', text: 'Choose your destination' },
    { icon: 'bi-globe2', text: 'AI plans step-by-step' },
    { icon: 'bi-journal-check', text: 'Get your itinerary' },
  ];

  return (
    <div className="container py-5 text-center" style={{ marginTop: '10vh' }}>
      <h1 className="display-5 fw-bold">Trip DVisor</h1>
      <h2 className="h4 fw-semibold mt-2">
        Welcome{username ? `, ${username}` : ''}!
      </h2>

      {isMobile ? (
        <>
          <p className="mt-3 mx-auto" style={{ maxWidth: '500px', fontSize: '0.95rem' }}>
            Plan smarter, travel better. Trip DVisor uses AI to help you create beautiful, customized itineraries — whether you're going solo or with a group.
          </p>
          <button className="btn btn-success btn-lg mt-3 px-4" onClick={goToPlanner}>
            <i className="bi bi-map-fill me-2"></i> New Trip
          </button>
          <div className="d-flex justify-content-center gap-3 mt-4 flex-wrap">
            {mobileCards.map(({ icon, text }, idx) => (
              <div
                key={idx}
                className="d-flex flex-column align-items-center justify-content-center border rounded p-3 shadow-sm"
                style={{ width: '100px', height: '100px' }}
              >
                <i className={`bi ${icon} text-primary fs-3 mb-2`}></i>
                <div style={{ fontSize: '0.85rem' }}>{text}</div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <>
          <p className="lead mt-4 mx-auto" style={{ maxWidth: '600px' }}>
            Trip DVisor is your intelligent travel companion.
            Create, customize, and optimize your travel plans using smart AI suggestions.
            Whether it's a solo trip or group adventure — we've got you covered!
          </p>
          <button className="btn btn-success btn-lg mt-4 px-5" onClick={goToPlanner}>
            <i className="bi bi-map-fill me-2"></i> Create a New Trip
          </button>
          <div className="row mt-5 justify-content-center">
            {desktopCards.map(({ icon, text }, idx) => (
              <div className="col-10 col-md-3 mb-3" key={idx}>
                <div className="card shadow-sm p-3">
                  <div className="text-primary mb-2">
                    <i className={`bi ${icon} fs-2`}></i>
                  </div>
                  <div className="fw-medium">{text}</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default HomePage;
