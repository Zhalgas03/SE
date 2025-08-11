import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocation } from 'react-router-dom';
function ResetPassword() {
  const location = useLocation();
const [form, setForm] = useState({
  email: location.state?.email || '',
  code: '',
  password: ''
});
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    setLoading(true);

    const { email, code, password } = form;

    if (!email || !code || !password) {
      setError('All fields are required');
      setLoading(false);
      return;
    }

    try {
      const res = await fetch('http://localhost:5001/api/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      const data = await res.json();
      if (data.success) {
        setMessage('Password successfully reset');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError(data.message || 'Reset failed');
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
        <h5 className="mt-3">Reset Password</h5>
      </div>

      <div className="mb-3">
        <label>Email</label>
        <input
          type="email"
          name="email"
          className="form-control"
          value={form.email}
          onChange={handleChange}
          required
        />
      </div>

      <div className="mb-3">
        <label>Reset Code</label>
        <input
          type="text"
          name="code"
          className="form-control"
          value={form.code}
          onChange={handleChange}
          required
        />
      </div>

      <div className="mb-3">
        <label>New Password</label>
        <input
          type="password"
          name="password"
          className="form-control"
          value={form.password}
          onChange={handleChange}
          required
        />
      </div>

      {error && <div className="alert alert-danger text-center">{error}</div>}
      {message && <div className="alert alert-success text-center">{message}</div>}

      <button type="submit" className="btn btn-success w-100" disabled={loading}>
        {loading ? 'Resetting...' : 'Reset Password'}
      </button>
    </form>
  );
}

export default ResetPassword;