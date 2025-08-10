// src/components/MobileMenu.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import './MobileMenu.css';

function MobileMenu({
  user,
  goToPlanner,
  handleLogout,
  onClose,
  isPremium,
  isAdmin,
  isDark,
  onToggleTheme,
  isClosing,
}) {
  let logoSrc = '/logo.png';
  if (isAdmin && isDark) logoSrc = '/admin_alt.png';
  else if (isAdmin) logoSrc = '/admin.png';
  else if (isPremium && isDark) logoSrc = '/premium_alt.png';
  else if (isPremium) logoSrc = '/premium.png';
  else if (isDark) logoSrc = '/logo_alt.png';

  return (
    <>
      {/* Overlay */}
      <div className="mm-overlay" onClick={onClose} />

      {/* Sheet */}
      <div className={`mm-sheet ${isClosing ? 'mm-closing' : 'mm-opening'}`}>
        {/* Header */}
        <div className="mm-header">
          <div className="mm-brand">
            <img src={logoSrc} alt="Trip DVisor" height="28" />
            {isAdmin && <span className="mm-badge mm-badge-admin">Admin</span>}
            {!isAdmin && isPremium && (
              <span className="mm-badge mm-badge-premium">Premium</span>
            )}
          </div>

          <div className="mm-actions">
            <button
              className="mm-icon-btn"
              aria-label="Toggle theme"
              onClick={onToggleTheme}
              title="Toggle theme"
            >
              <i className={`bi ${isDark ? 'bi-moon-stars-fill' : 'bi-brightness-high'}`} />
            </button>
            <button className="mm-icon-btn" aria-label="Close" onClick={onClose} title="Close">
              <i className="bi bi-x-lg" />
            </button>
          </div>
        </div>

        {/* Nav list */}
        <nav className="mm-list">
          <button
            className="mm-item"
            onClick={() => {
              goToPlanner();
              onClose();
            }}
          >
            <i className="bi bi-robot mm-ico" />
            <span>Planner</span>
          </button>

          <Link className="mm-item" to="/favorites" onClick={onClose}>
            <i className="bi bi-heart mm-ico" />
            <span>Favorites</span>
          </Link>

          {isAdmin && (
            <Link className="mm-item mm-item-accent" to="/admin" onClick={onClose}>
              <i className="bi bi-shield-lock mm-ico" />
              <span>Admin Panel</span>
            </Link>
          )}

          <div className="mm-sep" />

          {user ? (
            <>
              <Link className="mm-item" to="/account" onClick={onClose}>
                <i className="bi bi-person-circle mm-ico" />
                <span>{user.username}</span>
              </Link>
              <button
                className="mm-btn mm-btn-danger"
                onClick={() => {
                  handleLogout();
                  onClose();
                }}
              >
                Sign Out
              </button>
            </>
          ) : (
            <Link className="mm-btn mm-btn-primary" to="/login" onClick={onClose}>
              Sign In
            </Link>
          )}
        </nav>
      </div>
    </>
  );
}

export default MobileMenu;
