import React, { useEffect } from 'react';
import { useUser } from '../context/UserContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthRedirect } from '../hooks/useAuthRedirect'; // импорт хука

function HomePage() {
  const { setUser } = useUser();
  const navigate = useNavigate();
  const location = useLocation();
  const { goToPlanner } = useAuthRedirect(); // ⬅️ используем хук

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

  return (
    <div className="container py-5 text-center" style={{ marginTop: '15vh' }}>
      <h1 className="display-4 fw-bold">Trip DVisor</h1>
      <h2 className="h3 fw-semibold mt-2">
        Welcome{localStorage.getItem('username') ? `, ${localStorage.getItem('username')}` : ''}!
      </h2>

      <p className="lead mt-4 mx-auto" style={{ maxWidth: '600px' }}>
        Trip DVisor is your intelligent travel companion.
        Create, customize, and optimize your travel plans using smart AI suggestions.
        Whether it's a solo trip or group adventure — we've got you covered!
      </p>

      <button
        className="btn btn-success btn-lg mt-4 px-5"
        onClick={goToPlanner}
      >
        <i className="bi bi-map-fill me-2"></i> Create a New Trip
      </button>

      <div className="row mt-5 justify-content-center">
        {[
          { icon: 'bi-airplane-engines', text: 'Choose your destination' },
          { icon: 'bi-globe2', text: 'AI plans step-by-step' },
          { icon: 'bi-journal-check', text: 'Get your itinerary' },
        ].map(({ icon, text }, idx) => (
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
    </div>
  );
}

export default HomePage;
