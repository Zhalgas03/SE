import React, { useEffect, useState } from 'react';
import { useUser } from '../context/UserContext';
import { FaEye, FaEyeSlash } from 'react-icons/fa'; 
import AccountProfile from '../components/AccountProfile';
import AccountSubscription from '../components/AccountSubscription';
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
  <AccountProfile
    username={username}
    setUsername={setUsername}
    email={email}
    setEmail={setEmail}
    enable2FA={enable2FA}
    isToggling2FA={isToggling2FA}
    isSaving={isSaving}
    isChangingPassword={isChangingPassword}
    currentPassword={currentPassword}
    setCurrentPassword={setCurrentPassword}
    newPassword={newPassword}
    setNewPassword={setNewPassword}
    showNewPassword={showNewPassword}
    setShowNewPassword={setShowNewPassword}
    showCurrentPassword={showCurrentPassword}
    setShowCurrentPassword={setShowCurrentPassword}
    editingUsername={editingUsername}
    setEditingUsername={setEditingUsername}
    editingEmail={editingEmail}
    setEditingEmail={setEditingEmail}
    handleSave={handleSave}
    handleToggle2FA={handleToggle2FA}
    handleChangePassword={handleChangePassword}
    message={message}
  />
</div>

      {/* Правая колонка — подписка */}
<AccountSubscription
  isSubscribed={isSubscribed}
  isDarkTheme={isDarkTheme}
  handleSubscribe={handleSubscribe}
/>


    </div>
  </div>
);


}

export default AccountPage;
