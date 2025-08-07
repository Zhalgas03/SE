import React from 'react';
import { Link } from 'react-router-dom';

function MobileMenu({ user, goToPlanner, handleLogout, onClose }) {
  return (
    <div className="mobile-dropdown bg-white shadow px-4 py-3 animate-slide-down position-absolute top-100 start-0 w-100 z-2">
      <button className="btn btn-link nav-link text-start" onClick={() => { goToPlanner(); onClose(); }}>
        <i className="bi bi-robot me-1" /> Planner
      </button>

      <Link className="nav-link text-start" to="/favorites" onClick={onClose}>
        <i className="bi bi-heart me-1" /> Favorites
      </Link>

      {user && user.username && (
        <Link
          className="nav-link text-muted small ps-1 mt-1"
          to="/account"
          onClick={onClose}
          style={{ pointerEvents: 'auto' }}
        >
          <i className="bi bi-person-circle me-1" /> {user.username}
        </Link>
      )}

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
