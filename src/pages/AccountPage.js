import React, { useEffect, useState } from 'react';

function AccountPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

useEffect(() => {
  const token = localStorage.getItem('token');
  if (!token) return;

  fetch('http://localhost:5001/api/account/settings', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    credentials: 'include',
  })
  
    .then(res => {
      if (res.status === 401) {
        localStorage.clear();
        window.location.href = '/login';
        return null;
      }
      return res.json();
    })
    .then(data => {
      if (data?.success) {
        setUsername(data.data.username);
        setEmail(data.data.email);
      } else if (data) {
        setMessage(data.message || 'Failed to load');
      }
    })
    .catch(() => setMessage('Failed to load account info'));
}, []);


  return (
    <div className="container py-5" style={{ maxWidth: '500px' }}>
      <h2 className="mb-4">Account Settings</h2>

      {message && <div className="alert alert-info">{message}</div>}

      <div className="mb-3">
        <label className="form-label">Username</label>
        <input type="text" className="form-control" value={username} disabled />
      </div>

      <div className="mb-3">
        <label className="form-label">Email</label>
        <input type="email" className="form-control" value={email} disabled />
      </div>
    </div>
  );
}

export default AccountPage;
