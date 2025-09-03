import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { useAuthRedirect } from '../hooks/useAuthRedirect';
import BurgerMenu from './BurgerMenu';
import MobileMenu from './MobileMenu';
import './MobileMenu.css';

function Navbar() {
  // Вытаскиваем isPremium и isAdmin из контекста
  const { user, clearUser, isPremium, isAdmin } = useUser();
  const { goToPlanner } = useAuthRedirect();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [isDark, setIsDark] = useState(false);

  // Тема при монтировании
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

  // --- Выбор логотипа с учетом admin/premium/dark ---
  let logoSrc = '/logo.png';
  if (isAdmin && isDark) logoSrc = '/admin_alt.png';
  else if (isAdmin) logoSrc = '/admin.png';
  else if (isPremium && isDark) logoSrc = '/premium_alt.png';
  else if (isPremium) logoSrc = '/premium.png';
  else if (isDark) logoSrc = '/logo_alt.png';

  return (
    <div className="navbar-container position-relative z-3">
      <div className="navbar shadow-sm px-3 px-md-5 d-flex justify-content-between align-items-center"
           style={{ backgroundColor: 'var(--header-bg)' }}>
        {/* Логотип */}
        <Link className="navbar-brand fw-bold d-flex align-items-center" to="/">
          <img
            src={logoSrc}
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
              {isAdmin && (
                <Link
                  to="/admin"
                  className="btn btn-outline-warning btn-sm ms-2"
                  style={{
                    fontWeight: 600,
                    borderWidth: 2,
                    borderColor: '#ffc107',
                    color: '#9a7400',
                    letterSpacing: '0.02em'
                  }}
                >
                  Admin
                </Link>
              )}
              <button className="btn btn-outline-danger btn-sm ms-2" onClick={handleLogout}>
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
          isPremium={isPremium}
          isAdmin={isAdmin}
          isDark={isDark}
          onToggleTheme={handleToggleTheme}
        />
      )}
    </div>
  );
}

export default Navbar;
