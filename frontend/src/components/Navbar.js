import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { useAuthRedirect } from '../hooks/useAuthRedirect';
import BurgerMenu from './BurgerMenu';
import MobileMenu from './MobileMenu';
import './MobileMenu.css';

function Navbar() {
  const { user, clearUser } = useUser();
  const { goToPlanner } = useAuthRedirect();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const handleLogout = () => {
    clearUser();
    navigate('/login');
  };

  const handleCloseMenu = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsOpen(false);
      setIsClosing(false);
    }, 300);
  };

  return (
    <div className="navbar-container position-relative z-3">
      {/* Top bar: Logo + Burger */}
      <div className="navbar navbar-light bg-white shadow-sm px-3 px-md-5 d-flex justify-content-between align-items-center">
        <Link className="navbar-brand fw-bold d-flex align-items-center" to="/">
          <img src="/logo.png" alt="Trip DVisor Logo" height="30" className="me-2" />
        </Link>

        <div className="d-lg-none">
          <BurgerMenu isOpen={isOpen} toggle={() => setIsOpen(!isOpen)} />
        </div>

        {/* Desktop nav */}
        <div className="d-none d-lg-flex align-items-center gap-3">
          <button className="btn btn-link nav-link" onClick={goToPlanner}>
            <i className="bi bi-robot me-1" /> Planner
          </button>
          <Link className="nav-link" to="/favorites">
            <i className="bi bi-heart me-1" /> Favorites
          </Link>
          {user ? (
            <button className="btn btn-outline-danger btn-sm" onClick={handleLogout}>
              Sign Out
            </button>
          ) : (
            <Link className="btn btn-outline-primary btn-sm" to="/login">Sign In</Link>
          )}
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <MobileMenu
          user={user}
          goToPlanner={goToPlanner}
          handleLogout={handleLogout}
          onClose={handleCloseMenu}
          isClosing={isClosing}
        />
      )}
    </div>
  );
}

export default Navbar;