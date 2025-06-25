import React, { useEffect, useState } from 'react';
import { useUser } from '../context/UserContext';

function AccountPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [enable2FA, setEnable2FA] = useState(false);
  const [message, setMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const { setUser } = useUser();

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
        } else {
          setMessage(data.message || 'Failed to load user profile');
        }
      })
      .catch(() => setMessage('Server error while loading profile'));
  }, []);

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


  const handleToggle2FA = async () => {
    const token = localStorage.getItem('token');
    setMessage('');

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
    }
  };

  return (
    <div className="container py-5" style={{ maxWidth: '500px' }}>
      <h2 className="mb-4">Account Settings</h2>

      {message && <div className="alert alert-info">{message}</div>}

      <div className="mb-3">
        <label className="form-label">Username</label>
        <input
          type="text"
          className="form-control"
          value={username}
          onChange={e => setUsername(e.target.value)}
        />
      </div>

      <div className="mb-3">
        <label className="form-label">Email</label>
        <input
          type="email"
          className="form-control"
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
      </div>

      <div className="form-check form-switch mb-4">
        <input
          className="form-check-input"
          type="checkbox"
          checked={enable2FA}
          onChange={handleToggle2FA}
          id="enable2FA"
        />
        <label className="form-check-label" htmlFor="enable2FA">
          Enable Two-Factor Authentication (2FA)
        </label>
      </div>

      <button
        onClick={handleSave}
        className="btn btn-primary"
        disabled={isSaving}
      >
        {isSaving ? 'Saving...' : 'Save Changes'}
      </button>
    </div>
  );
}

export default AccountPage;
