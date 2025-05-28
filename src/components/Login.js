import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState("");
  const [emailError, setEmailError] = useState("");
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

  const handleSubmit = async e => {
    e.preventDefault();
    setError("");

    if (!emailRegex.test(form.email)) {
      setEmailError("Please enter a valid email address.");
      return;
    }

    try {
      const res = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });

      const data = await res.json();
      console.log("SERVER RESPONSE:", data);

      if (data.success) {
        setUser({ email: form.email, username: data.username });
        navigate('/');
      } else {
        setError(data.message || "Login failed");
      }
    } catch (err) {
      setError("Network error. Try again.");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4"
      style={{ width: '100%', maxWidth: '400px' }}
    >
      <h2 className="text-center mb-4 fw-bold">Welcome</h2>

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
