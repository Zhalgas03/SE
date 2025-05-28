import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

function Register() {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const isPasswordStrong = password => {
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return regex.test(password);
  };

  const handleSubmit = async e => {
    e.preventDefault();

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!isPasswordStrong(form.password)) {
      setError('Password must be at least 8 characters and include uppercase, lowercase letters, and a number');
      return;
    }

    const payload = {
      username: form.username,
      email: form.email,
      password: form.password
    };

    try {
      const res = await fetch("http://localhost:5000/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include"
      });

      const data = await res.json();
      console.log("SERVER RESPONSE:", data);

      if (res.ok && data.success) {
        navigate('/login');
      } else {
        setError(data.message || 'Registration failed');
      }
    } catch (err) {
      console.error(err);
      setError('Network error');
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4"
      style={{ width: '100%', maxWidth: '400px' }}
    >
      <h2 className="text-center mb-4 fw-bold">Create Account</h2>

      <div className="mb-3">
        <label>Username</label>
        <input
          name="username"
          type="text"
          className="form-control"
          onChange={handleChange}
          required
        />
      </div>

      <div className="mb-3">
        <label>Email</label>
        <input
          name="email"
          type="email"
          className="form-control"
          onChange={handleChange}
          required
        />
      </div>

      <div className="mb-1">
        <label>Password</label>
        <input
          name="password"
          type="password"
          className="form-control"
          onChange={handleChange}
          required
        />
      </div>

      <div className="mb-3 text-muted" style={{ fontSize: "0.85em" }}>
        Password must be at least 8 characters and include uppercase, lowercase letters, and a number
      </div>

      <div className="mb-3">
        <label>Confirm Password</label>
        <input
          name="confirmPassword"
          type="password"
          className="form-control"
          onChange={handleChange}
          required
        />
      </div>

{error && (
  <div
    className="alert alert-danger d-flex align-items-center mt-3"
    role="alert"
    style={{
      fontSize: "0.9em",
      padding: "0.75rem 1rem",
      borderRadius: "0.375rem",
      boxShadow: "0 0 6px rgba(0,0,0,0.1)"
    }}
  >
    <span className="me-2">⚠️</span> {error}
  </div>
)}

      <button type="submit" className="btn btn-primary w-100">
        Sign Up
      </button>

      <p className="text-center mt-3">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </form>
  );
}

export default Register;
