import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!email.trim()) {
      setError('Email is required');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('http://localhost:5001/api/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await res.json();
if (data.success) {
  navigate('/reset-password', { state: { email } });
} else {
        setError(data.message || 'Failed to send reset code');
      }
    } catch (err) {
      setError('Network error. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4"
      style={{ width: '100%', maxWidth: '400px', margin: '0 auto' }}
    >
      <div className="text-center mb-3">
        <img src="/logo.png" alt="Trip DVisor" style={{ height: '50px' }} />
        <h5 className="mt-3">Forgot Password</h5>
      </div>

      <div className="mb-3">
        <label>Email</label>
        <input
          type="email"
          className="form-control"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>

      {error && <div className="alert alert-danger text-center">{error}</div>}
      {message && <div className="alert alert-success text-center">{message}</div>}

      <button type="submit" className="btn btn-primary w-100" disabled={loading}>
        {loading ? 'Sending...' : 'Send Reset Code'}
      </button>

      <p className="text-center mt-3">
        Back to <span className="text-primary" style={{ cursor: 'pointer' }} onClick={() => navigate('/login')}>Login</span>
      </p>
    </form>
  );
}

export default ForgotPassword;