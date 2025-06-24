import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { useAuthRedirect } from '../hooks/useAuthRedirect';

function Navbar() {
  const { user, clearUser } = useUser();
  const navigate = useNavigate();
  const { goToPlanner } = useAuthRedirect();
  const handleLogout = () => {
    clearUser();
    navigate('/login');
  };

  return (
  <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm px-5">
            <Link className="navbar-brand fw-bold d-flex align-items-center" to="/">
        <img
          src="/logo.png"
          alt="Trip DVisor Logo"
          height="30"
          className="me-2"
        />
  
      </Link>

      <div className="ms-auto d-flex align-items-center">
        <div className="me-4 d-flex">
<button className="btn btn-link nav-link me-3 p-0" onClick={goToPlanner}>
  <i className="bi bi-robot me-1"></i> Planner
</button>
          
          <Link className="nav-link" to="/favorites">
            <i className="bi bi-heart me-1"></i> Favorites
          </Link>
        </div>
        {user ? (
          <button className="btn btn-outline-danger btn-sm" onClick={handleLogout}>
            Sign Out
          </button>
        ) : (
          <Link className="btn btn-outline-primary btn-sm" to="/login">Sign In</Link>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
