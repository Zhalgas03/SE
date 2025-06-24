import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ReCAPTCHA from 'react-google-recaptcha';

function Register() {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [captchaToken, setCaptchaToken] = useState('');
  const recaptchaRef = useRef(null);
  const navigate = useNavigate();

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const isPasswordStrong = password => {
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return regex.test(password);
  };

  const handleCaptchaChange = token => {
    setCaptchaToken(token);
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

    if (!captchaToken) {
      setError('Please complete the CAPTCHA.');
      return;
    }

    const payload = {
      username: form.username,
      email: form.email,
      password: form.password,
      captchaToken
    };

    try {
      const res = await fetch("http://localhost:5001/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include"
      });

      const data = await res.json();
      console.log("SERVER RESPONSE:", data);

      if (res.ok && data.success) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('username', data.username);
        navigate('/login');
      } else {
        setError(data.message || 'Registration failed');
        recaptchaRef.current.reset();
        setCaptchaToken('');
      }
    } catch (err) {
      console.error(err);
      setError('Network error');
      recaptchaRef.current.reset();
      setCaptchaToken('');
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = 'http://localhost:5001/api/auth/google';
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4"
      style={{ width: '100%', maxWidth: '400px' }}
    >
      <div className="text-center mb-3">
        <img src="/logo.png" alt="Trip DVisor" style={{ height: '50px' }} />
      </div>

      <div className="mb-3">
        <button
          type="button"
          className="btn btn-outline-dark w-100 google-btn"
          onClick={handleGoogleLogin}
          style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px" }}
        >
          <img
            src="https://developers.google.com/identity/images/g-logo.png"
            alt="Google"
            width="20"
            height="20"
          />
          Sign up with Google
        </button>
      </div>
<div className="mb-3 d-grid">
  <button
    type="button"
    className="btn btn-outline-dark"
    onClick={() => window.location.href = "http://localhost:5001/github"}
    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
  >
    <img
      src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
      alt="GitHub"
      width="20"
      height="20"
    />
    Sign in with GitHub
  </button>
</div>
      <hr className="my-4" style={{ opacity: 0.3 }} />

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

      <div className="mb-3">
        <ReCAPTCHA
          ref={recaptchaRef}
          sitekey="6LdTZGwrAAAAAOs5n3cyHEAebDLsfRcyMd4-Fj67"
          onChange={handleCaptchaChange}
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
