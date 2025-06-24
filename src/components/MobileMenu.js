import React from 'react';
import { Link } from 'react-router-dom';

function MobileMenu({ user, goToPlanner, handleLogout, onClose }) {
  return (
    <div className="mobile-dropdown bg-white shadow px-4 py-3 animate-slide-down position-absolute top-100 start-0 w-100 z-2">
      <button className="btn btn-link nav-link" onClick={() => { goToPlanner(); onClose(); }}>
        <i className="bi bi-robot me-1" /> Planner
      </button>

      <Link className="nav-link" to="/favorites" onClick={onClose}>
        <i className="bi bi-heart me-1" /> Favorites
      </Link>

      {user ? (
        <button className="btn btn-outline-danger btn-sm mt-2" onClick={() => { handleLogout(); onClose(); }}>
          Sign Out
        </button>
      ) : (
        <Link className="btn btn-outline-primary btn-sm mt-2" to="/login" onClick={onClose}>
          Sign In
        </Link>
      )}
    </div>
  );
}

export default MobileMenu;
