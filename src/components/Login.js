import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import ReCAPTCHA from 'react-google-recaptcha';

function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [captchaToken, setCaptchaToken] = useState("");
  const recaptchaRef = useRef(null);

  const { setUser } = useUser();
  const navigate = useNavigate();

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));

    if (name === "email") {
      if (value === "") {
        setEmailError("");
      } else if (!emailRegex.test(value)) {
        setEmailError("Please enter a valid email address.");
      } else {
        setEmailError("");
      }
    }
  };

  const handleCaptchaChange = token => {
    setCaptchaToken(token);
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setError("");

    if (!captchaToken) {
      setError("Please complete the CAPTCHA.");
      return;
    }

    if (!emailRegex.test(form.email)) {
      setEmailError("Please enter a valid email address.");
      return;
    }

    try {
      const res = await fetch("http://localhost:5001/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, captchaToken }),
        credentials: "include"
      });

      const data = await res.json();
      console.log("SERVER RESPONSE:", data);

if (data.success) {
  setUser({ email: form.email, username: data.username }, data.token);
  navigate('/');
}else {
        setError(data.message || "Login failed");
        recaptchaRef.current.reset();
        setCaptchaToken('');
      }
    } catch (err) {
      setError("Network error. Try again.");
      recaptchaRef.current.reset();
      setCaptchaToken('');
    }
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

      <div className="mb-3 d-grid">
        <a
          className="btn btn-outline-dark google-btn"
          href="https://3955-192-167-110-47.ngrok-free.app"
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
        >
          <img
            src="https://developers.google.com/identity/images/g-logo.png"
            alt="Google"
            width="20"
            height="20"
          />
          Sign in with Google
        </a>
      </div>
<div className="mb-3 d-grid">
  <button
    className="btn btn-outline-dark"
    onClick={() => window.location.href = "http://localhost:5001/api/github"}
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
        <label>Email</label>
        <input
          name="email"
          type="email"
          className={`form-control ${emailError ? "is-invalid" : ""}`}
          onChange={handleChange}
          required
        />
        {emailError && (
          <div className="invalid-feedback">{emailError}</div>
        )}
      </div>

      <div className="mb-3">
        <label>Password</label>
        <input
          name="password"
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
        <div className="alert alert-danger text-center" role="alert">
          {error}
        </div>
      )}

      <button type="submit" className="btn btn-primary w-100">
        Sign In
      </button>

      <p className="text-center mt-3">
        Don’t have an account? <Link to="/register">Sign up</Link>
      </p>
    </form>
  );
}

export default Login;
