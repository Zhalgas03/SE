import React, { useState, useEffect } from 'react';
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
  const [isDark, setIsDark] = useState(false);

  // Load saved theme on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      document.body.classList.add('dark-theme');
      setIsDark(true);
    }
  }, []);

  const handleToggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    if (newTheme) {
      document.body.classList.add('dark-theme');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark-theme');
      localStorage.setItem('theme', 'light');
    }
  };

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
      <div className="navbar shadow-sm px-3 px-md-5 d-flex justify-content-between align-items-center"
           style={{ backgroundColor: 'var(--header-bg)' }}>
        {/* Logo */}
        <Link className="navbar-brand fw-bold d-flex align-items-center" to="/">
        <img
  src={isDark ? '/logo_alt.png' : '/logo.png'}
  alt="Trip DVisor Logo"
  height="32"
  className="me-2"
  style={{ marginTop: '2px' }}
/>
        </Link>

        {/* Desktop nav */}
        <div className="d-none d-lg-flex align-items-center gap-3">
          <button className="btn btn-link nav-link" onClick={goToPlanner} style={{ color: 'var(--text-color)' }}>
            Planner
          </button>
          <Link className="nav-link" to="/favorites" style={{ color: 'var(--text-color)' }}>
            Favorites
          </Link>

<button
  onClick={handleToggleTheme}
  className="btn p-0 border-0 bg-transparent"
  style={{
    color: 'var(--text-color)',
    boxShadow: 'none',
  }}
>
  <i className={`bi ${isDark ? 'bi-moon-stars-fill' : 'bi-brightness-high'}`} style={{ fontSize: '1rem' }} />
</button>


          {user ? (
            <>
              <Link
                to="/account"
                className="nav-link d-flex align-items-center"
                style={{ fontWeight: '500', color: 'var(--text-color)' }}
              >
                
                {user.username}
              </Link>
              <button className="btn btn-outline-danger btn-sm" onClick={handleLogout}>
                Sign Out
              </button>
            </>
          ) : (
            <Link className="btn btn-outline-primary btn-sm" to="/login">Sign In</Link>
          )}
        </div>

        {/* Mobile burger */}
        <div className="d-lg-none">
          <BurgerMenu isOpen={isOpen} toggle={() => setIsOpen(!isOpen)} />
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
