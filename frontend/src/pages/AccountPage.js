// src/pages/AccountPage.jsx
import React, { useEffect, useState } from 'react';
import { useUser } from '../context/UserContext';
import AccountLeft from '../components/AccountLeft';
import AccountRight from '../components/AccountRight';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5001';
const redirectToLogin = () => {
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  window.location.href = `/login?next=${next}`;
};

function AccountPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [enable2FA, setEnable2FA] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [weeklyTripOptIn, setWeeklyTripOptIn] = useState(false);
  const [message, setMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const { setUser, isPremium } = useUser();

  const [isToggling2FA, setIsToggling2FA] = useState(false);
  const [isDarkTheme, setIsDarkTheme] = useState(() =>
    document.body.classList.contains('dark-theme')
  );

  const [editingUsername, setEditingUsername] = useState(false);
  const [editingEmail, setEditingEmail] = useState(false);

  // watch theme changes
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDarkTheme(document.body.classList.contains('dark-theme'));
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  // --- AUTH GUARD + profile load ---
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      // not logged in → go to login and come back here
      redirectToLogin();
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/user/profile`, {
          headers: { Authorization: `Bearer ${token}` },
          credentials: 'include',
        });

        if (res.status === 401) {
          // expired/invalid token → clean and login
          localStorage.removeItem('token');
          redirectToLogin();
          return;
        }

        const data = await res.json();
        if (cancelled) return;

        if (data.success && data.user) {
          setUsername(data.user.username || '');
          setEmail(data.user.email || '');
          setEnable2FA(!!data.user.is_2fa_enabled);
          setIsSubscribed(!!data.user.is_subscribed);
          const opt = data.user.weekly_trip_opt_in;
          setWeeklyTripOptIn(opt === true || opt === 'true');
        } else {
          // unexpected shape, show gentle message but keep page
          setMessage(data.message || 'Failed to load user profile');
        }
      } catch (e) {
        if (!cancelled) setMessage('Server error while loading profile');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, []);

  // save username/email
  const handleSave = async () => {
    const token = localStorage.getItem('token');
    setIsSaving(true);
    setMessage('');

    try {
      const res = await fetch(`${API_BASE}/api/user/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify({ username, email }),
      });

      if (res.status === 401) {
        localStorage.removeItem('token');
        redirectToLogin();
        return;
      }

      const data = await res.json();
      if (data.success) {
        setMessage(data.message || 'Profile updated');
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

  // toggle 2FA
  const handleToggle2FA = async () => {
    const token = localStorage.getItem('token');
    setMessage('');
    setIsToggling2FA(true);
    const start = Date.now();

    try {
      const res = await fetch(`${API_BASE}/api/user/2fa/enable-disable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify({ enable_2fa: !enable2FA }),
      });

      if (res.status === 401) {
        localStorage.removeItem('token');
        redirectToLogin();
        return;
      }

      const data = await res.json();
      if (data.success) {
        setEnable2FA(prev => !prev);
        setMessage(data.message || '2FA updated');
      } else {
        setMessage(data.message || 'Failed to update 2FA');
      }
    } catch {
      setMessage('Server error while updating 2FA');
    } finally {
      const elapsed = Date.now() - start;
      const delay = Math.max(300 - elapsed, 0);
      setTimeout(() => setIsToggling2FA(false), delay);
    }
  };

  // change password
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
      const res = await fetch(`${API_BASE}/api/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ currentPassword, newPassword }),
      });

      if (res.status === 401) {
        localStorage.removeItem('token');
        redirectToLogin();
        return;
      }

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

  // start subscription (Stripe)
  const handleSubscribe = async () => {
    const token = localStorage.getItem('token');
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/pay/create-checkout-session`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        credentials: 'include',
      });

      if (res.status === 401) {
        localStorage.removeItem('token');
        redirectToLogin();
        return;
      }

      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        setMessage(data.error || 'Failed to start subscription process');
      }
    } catch {
      setMessage('Server error during subscription');
    }
  };

  // toggle weekly trip emails (premium only)
  const [isTogglingWeekly, setIsTogglingWeekly] = useState(false);
  const handleToggleWeeklyTrip = async () => {
    if (!isPremium) return;
    const token = localStorage.getItem('token');
    setIsTogglingWeekly(true);
    setMessage('');

    const next = !weeklyTripOptIn;
    setWeeklyTripOptIn(next); // optimistic

    try {
      const res = await fetch(`${API_BASE}/api/user/weekly-trip-opt-in`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ opt_in: next }),
      });

      if (res.status === 401) {
        localStorage.removeItem('token');
        redirectToLogin();
        return;
      }

      const data = await res.json();
      if (!data.success) {
        setWeeklyTripOptIn(!next); // rollback
        setMessage(data.message || 'Failed to update weekly trip preference');
      } else {
        setMessage('Weekly trip preference updated');
      }
    } catch {
      setWeeklyTripOptIn(!next);
      setMessage('Server error while updating weekly trip preference');
    } finally {
      setIsTogglingWeekly(false);
    }
  };

  // UI
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
        <div className="col-md-5">
          <AccountLeft
            // data
            username={username}
            email={email}
            enable2FA={enable2FA}
            message={message}
            // edit states
            editingUsername={editingUsername}
            setEditingUsername={setEditingUsername}
            editingEmail={editingEmail}
            setEditingEmail={setEditingEmail}
            // setters
            setUsername={setUsername}
            setEmail={setEmail}
            // save
            onSave={handleSave}
            isSaving={isSaving}
            // 2FA
            onToggle2FA={handleToggle2FA}
            isToggling2FA={isToggling2FA}
            // password
            currentPassword={currentPassword}
            setCurrentPassword={setCurrentPassword}
            newPassword={newPassword}
            setNewPassword={setNewPassword}
            onChangePassword={handleChangePassword}
            isChangingPassword={isChangingPassword}
            // premium + weekly trips
            isPremium={isPremium}
            weeklyTripOptIn={weeklyTripOptIn}
            onToggleWeeklyTrip={handleToggleWeeklyTrip}
            isTogglingWeekly={isTogglingWeekly}
          />
        </div>

        <div className="col-md-7">
          <AccountRight
            isSubscribed={isSubscribed}
            onSubscribe={handleSubscribe}
            isDarkTheme={isDarkTheme}
            isPremium={isPremium}
          />
        </div>
      </div>
    </div>
  );
}

export default AccountPage;
