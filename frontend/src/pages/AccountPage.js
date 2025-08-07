import React, { useEffect, useState } from 'react';
import { useUser } from '../context/UserContext';
import { FaEye, FaEyeSlash } from 'react-icons/fa'; 

function AccountPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [enable2FA, setEnable2FA] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [message, setMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
const [currentPassword, setCurrentPassword] = useState('');
const [newPassword, setNewPassword] = useState('');
const [isChangingPassword, setIsChangingPassword] = useState(false);
  const { setUser } = useUser();
const [showNewPassword, setShowNewPassword] = useState(false);
const [showCurrentPassword, setShowCurrentPassword] = useState(false);

const [editingUsername, setEditingUsername] = useState(false);
const [editingEmail, setEditingEmail] = useState(false);

const [isToggling2FA, setIsToggling2FA] = useState(false);
const [isDarkTheme, setIsDarkTheme] = useState(() =>
  document.body.classList.contains('dark-theme')
);

useEffect(() => {
  const observer = new MutationObserver(() => {
    setIsDarkTheme(document.body.classList.contains('dark-theme'));
  });

  observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });

  return () => observer.disconnect(); // Очистка при размонтировании
}, []);
  // 🔹 Получение профиля
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    fetch('http://localhost:5001/api/user/profile', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      credentials: 'include',
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setUsername(data.user.username);
          setEmail(data.user.email);
          setEnable2FA(data.user.is_2fa_enabled);
          setIsSubscribed(data.user.is_subscribed);
        } else {
          setMessage(data.message || 'Failed to load user profile');
        }
        setIsLoading(false);
      })
      .catch(() => {
        setMessage('Server error while loading profile');
        setIsLoading(false);
      });
  }, []);
const handleChangePassword = async () => {
  const token = localStorage.getItem('token');
  setIsChangingPassword(true);
  setMessage('');

  if (!currentPassword || !newPassword) {
    setMessage('Please fill in both password fields');
    setIsChangingPassword(false);
    return;
  }

  if (newPassword.length < 8 || !/\d/.test(newPassword)) {
    setMessage('New password must be at least 8 characters and contain a digit');
    setIsChangingPassword(false);
    return;
  }

  try {
    const res = await fetch('http://localhost:5001/api/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        currentPassword,
        newPassword,
      }),
    });

    const data = await res.json();
    if (data.success) {
      setMessage('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
    } else {
      setMessage(data.message || 'Password change failed');
    }
  } catch {
    setMessage('Server error while changing password');
  } finally {
    setIsChangingPassword(false);
  }
};

  // 🔹 Сохранение профиля
  const handleSave = async () => {
    const token = localStorage.getItem('token');
    setIsSaving(true);
    setMessage('');

    try {
      const res = await fetch('http://localhost:5001/api/user/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify({ username, email }),
      });

      const data = await res.json();
      if (data.success) {
        setMessage(data.message);
        if (data.token && data.username) {
          setUser({ username: data.username }, data.token);
        }
      } else {
        setMessage(data.message || 'Update failed');
      }
    } catch {
      setMessage('Server error while updating profile');
    } finally {
      setIsSaving(false);
    }
  };

  // 🔹 Переключение 2FA
const handleToggle2FA = async () => {
  const token = localStorage.getItem('token');
  setMessage('');
  setIsToggling2FA(true); // ✅ Показать спиннер сразу

  const start = Date.now(); // ⏱ Начало

  try {
    const res = await fetch('http://localhost:5001/api/user/2fa/enable-disable', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      credentials: 'include',
      body: JSON.stringify({ enable_2fa: !enable2FA }),
    });

    const data = await res.json();
    if (data.success) {
      setEnable2FA(prev => !prev);
      setMessage(data.message);
    } else {
      setMessage(data.message || 'Failed to update 2FA');
    }
  } catch {
    setMessage('Server error while updating 2FA');
  } finally {
    const elapsed = Date.now() - start;
    const delay = Math.max(300 - elapsed, 0); // ⏳ не меньше 300мс

    setTimeout(() => {
      setIsToggling2FA(false);
    }, delay);
  }
};


  // 🔹 Stripe подписка
  const handleSubscribe = async () => {
    const token = localStorage.getItem('token');
    setMessage('');

    try {
      const res = await fetch('http://localhost:5001/api/pay/create-checkout-session', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
      });

      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        setMessage(data.error || 'Failed to start subscription process');
      }
    } catch (err) {
      setMessage('Server error during subscription');
    }
  };

  // 🔹 Показываем спиннер при загрузке
  if (isLoading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

return (
  <div className="container py-5" style={{ maxWidth: '1000px' }}>
    <div className="row g-4">
      {/* Левая колонка — профиль */}
      <div className="col-md-5">
        <div className="card shadow-sm rounded-4 p-4">
          <h4 className="mb-4 fw-bold">Account Settings</h4>

          {message && <div className="alert alert-info">{message}</div>}

<div className="mb-3">
  <label className="form-label">Username</label>
  {!editingUsername ? (
    <div
      className="form-control bg-light"
      style={{ cursor: 'pointer' }}
      onClick={() => setEditingUsername(true)}
    >
      {username || '—'}
    </div>
  ) : (
    <input
      type="text"
      className="form-control"
      placeholder={username}
      value={username}
      onChange={(e) => setUsername(e.target.value)}
      onBlur={() => setEditingUsername(false)}
      autoFocus
    />
  )}
</div>

<div className="mb-3">
  <label className="form-label">Email</label>
  {!editingEmail ? (
    <div
      className="form-control bg-light"
      style={{ cursor: 'pointer' }}
      onClick={() => setEditingEmail(true)}
    >
      {email || '—'}
    </div>
  ) : (
    <input
      type="email"
      className="form-control"
      placeholder={email}
      value={email}
      onChange={(e) => setEmail(e.target.value)}
      onBlur={() => setEditingEmail(false)}
      autoFocus
    />
  )}
</div>
<div className="form-check form-switch mb-4 d-flex align-items-center gap-3">
  <input
    className="form-check-input"
    type="checkbox"
    id="enable2FA"
    checked={enable2FA}
    onChange={handleToggle2FA}
    disabled={isToggling2FA} // 🔒 Заблокировано во время запроса
  />
  <label className="form-check-label mb-0" htmlFor="enable2FA">
    Enable Two-Factor Authentication (2FA)
  </label>

  {isToggling2FA && (
    <div
      className="spinner-border spinner-border-sm text-secondary ms-2"
      role="status"
      style={{ width: '1rem', height: '1rem' }}
    />
  )}
</div>

          <button
            onClick={handleSave}
            className="btn btn-primary w-100"
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>

          {/* 🔽 Новая секция смены пароля */}
          <hr className="my-4" />
          <h5 className="fw-bold mb-3">Change Password</h5>

<div className="mb-3 position-relative">
  <label className="form-label">Current Password</label>
  <input
    type={showCurrentPassword ? "text" : "password"}
    className="form-control pe-5"
    value={currentPassword}
    onChange={(e) => setCurrentPassword(e.target.value)}
  />
  <span
    className="position-absolute"
    style={{
      top: '70%',
      right: '12px',
      transform: 'translateY(-50%)',
      cursor: 'pointer',
      color: '#888',
      fontSize: '1.1rem',
      lineHeight: '1'
    }}
    onClick={() => setShowCurrentPassword(prev => !prev)}
  >
    {showCurrentPassword ? <FaEyeSlash /> : <FaEye />}
  </span>
</div>


<div className="mb-3 position-relative">
  <label className="form-label">New Password</label>
  <input
    type={showNewPassword ? "text" : "password"}
    className="form-control pe-5"
    value={newPassword}
    onChange={(e) => setNewPassword(e.target.value)}
  />
  <span
    className="position-absolute"
    style={{
      top: '70%',
      right: '12px',
      transform: 'translateY(-50%)',
      cursor: 'pointer',
      color: '#888',
      fontSize: '1.1rem',
      lineHeight: '1'
    }}
    onClick={() => setShowNewPassword(prev => !prev)}
  >
    {showNewPassword ? <FaEyeSlash /> : <FaEye />}
  </span>
</div>


          <button
            onClick={handleChangePassword}
            className="btn btn-outline-dark w-100"
            disabled={isChangingPassword}
          >
            {isChangingPassword ? 'Changing...' : 'Change Password'}
          </button>
        </div>
      </div>

      {/* Правая колонка — подписка */}
 <div className="col-md-7">
  {!isSubscribed ? (
    <div className="premium-wrapper-light p-4 rounded-4 bg-white shadow-sm">
      <h4 className="mb-4 text-center fw-bold fs-4 text-dark">Upgrade to Premium</h4>
      <div className="row row-cols-1 row-cols-md-2 g-2">

{/* INDIVIDUAL PLAN */}
<div className="col">
  <div className="premium-card-light d-flex flex-column rounded-4 p-4 h-100 border text-start">
    <img
  src={isDarkTheme ? 'premium_alt.png' : 'premium.png'}
  alt="Premium"
  className="logo-premium"
/>
    <h4 className="fw-bold text-primary">Individual</h4>
    <p className="text-muted mb-3">€5.00 / month</p>
    <hr />
    <ul className="list-unstyled mb-4 small text-dark">
      <li>• 1 Premium account</li>
      <li>• Weekly AI travel plans</li>
      <li>• Voting access & early features</li>
      <li>• Cancel anytime</li>
    </ul>
    <button className="btn btn-primary rounded-pill fw-semibold mt-auto" onClick={handleSubscribe}>
      Get Premium
    </button>
    <p className="mt-3 text-muted small">
      €0 for 1 month, then €5.00/month after. Cancel anytime.
    </p>
  </div>
</div>

        {/* DUO PLAN */}
<div className="col">
  <div className="premium-card-light d-flex flex-column rounded-4 p-4 h-100 border text-start">
    <img
  src={isDarkTheme ? 'premium_alt.png' : 'premium.png'}
  alt="Premium"
  className="logo-premium"
/>
    <h4 className="fw-bold text-success">Duo</h4>
    <p className="text-muted mb-3">€8.00 / month</p>
    <hr />
    <ul className="list-unstyled mb-4 small text-dark">
      <li>• 2 Premium accounts</li>
      <li>• Shared AI travel planner</li>
      <li>• Early access features</li>
      <li>• Cancel anytime</li>
    </ul>
    <button className="btn btn-outline-success rounded-pill fw-semibold mt-auto" disabled>
      Coming Soon
    </button>
    <p className="mt-3 text-muted small">
      For couples who live together. Available soon.
    </p>
  </div>
</div>


      </div>
    </div>
  ) : (
    <div className="alert alert-success mt-3 text-center fw-semibold fs-5">
      🎉 You are a Premium user
    </div>
  )}
</div>

    </div>
  </div>
);


}

export default AccountPage;
