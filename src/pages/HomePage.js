import React, { useEffect } from 'react';
import { useUser } from '../context/UserContext';
import { useNavigate, useLocation } from 'react-router-dom';

function HomePage() {
  const { user, setUser } = useUser();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get('token');
    const username = params.get('username');

    if (token && username) {
      setUser({ token, username });
      localStorage.setItem('token', token);
      localStorage.setItem('username', username);
      navigate('/', { replace: true }); // 🔁 Clean URL
    }
  }, [location, navigate, setUser]);

  const handleCreateTrip = () => {
    navigate(user ? '/planner' : '/login');
  };

  return (
    <div className="d-flex flex-column align-items-center justify-content-center text-center" style={{ height: '80vh' }}>
      <h1 className="display-4 fw-bold">
        Welcome{user ? `, ${user.username}` : ''}!
      </h1>
      <p className="lead mt-3" style={{ maxWidth: '600px' }}>
        Trip DVisor is your intelligent travel companion.
        Create, customize, and optimize your travel plans using smart AI suggestions.
        Whether it's a solo trip or group adventure — we've got you covered!
      </p>
      <button className="btn btn-success btn-lg mt-4 px-5" onClick={handleCreateTrip}>
        <i className="bi bi-map-fill me-2"></i> Create a New Trip
      </button>
    </div>
  );
}

export default HomePage;
