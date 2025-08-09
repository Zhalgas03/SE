import React from 'react';
import { Link } from 'react-router-dom';

// Прокидываем все нужные пропсы
function MobileMenu({
  user,
  goToPlanner,
  handleLogout,
  onClose,
  isPremium,
  isAdmin,
  isDark
}) {
  // Логотип для мобилки (можно показать наверху меню)
  let logoSrc = '/logo.png';
  if (isAdmin && isDark) logoSrc = '/admin_alt.png';
  else if (isAdmin) logoSrc = '/admin.png';
  else if (isPremium && isDark) logoSrc = '/premium_alt.png';
  else if (isPremium) logoSrc = '/premium.png';
  else if (isDark) logoSrc = '/logo_alt.png';

  return (
    <div className={`mobile-dropdown shadow px-4 py-3 animate-slide-down position-absolute top-100 start-0 w-100 z-2 ${isDark ? 'bg-dark' : 'bg-white'}`}>
      {/* Логотип и роль (не обязательно, по желанию) */}
      <div className="d-flex align-items-center mb-3">
        <img src={logoSrc} alt="Trip DVisor Logo" height="30" className="me-2" style={{ marginTop: '1px' }} />
        {isAdmin && (
          <span className="badge bg-danger ms-1" style={{ fontSize: '0.8rem' }}>Admin</span>
        )}
        {isPremium && !isAdmin && (
          <span className="badge bg-primary ms-1" style={{ fontSize: '0.8rem' }}>Premium</span>
        )}
      </div>

      {/* Навигация */}
      <button
        className={`btn btn-link nav-link text-start ${isDark ? 'text-light' : ''}`}
        onClick={() => { goToPlanner(); onClose(); }}
      >
        <i className="bi bi-robot me-1" /> Planner
      </button>

      <Link
        className={`nav-link text-start ${isDark ? 'text-light' : ''}`}
        to="/favorites"
        onClick={onClose}
      >
        <i className="bi bi-heart me-1" /> Favorites
      </Link>

      {/* Ссылка на админ-панель */}
      {isAdmin && (
        <Link
          className={`nav-link text-start ${isDark ? 'text-warning' : 'text-danger'} fw-bold`}
          to="/admin"
          onClick={onClose}
        >
          <i className="bi bi-shield-lock me-1" /> Admin Panel
        </Link>
      )}

      {/* Аккаунт пользователя */}
      {user && user.username && (
        <Link
          className={`nav-link text-muted small ps-1 mt-1 ${isDark ? 'text-light' : ''}`}
          to="/account"
          onClick={onClose}
          style={{ pointerEvents: 'auto' }}
        >
          <i className="bi bi-person-circle me-1" /> {user.username}
        </Link>
      )}

      {/* Кнопки входа/выхода */}
      {user ? (
        <button
          className="btn btn-outline-danger btn-sm mt-2"
          onClick={() => { handleLogout(); onClose(); }}
        >
          Sign Out
        </button>
      ) : (
        <Link
          className="btn btn-outline-primary btn-sm mt-2"
          to="/login"
          onClick={onClose}
        >
          Sign In
        </Link>
      )}
    </div>
  );
}

export default MobileMenu;
