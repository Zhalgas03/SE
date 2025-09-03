import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import ReCAPTCHA from 'react-google-recaptcha';
import { FaEye, FaEyeSlash } from 'react-icons/fa';

function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [captchaToken, setCaptchaToken] = useState("");
  const [show2FA, setShow2FA] = useState(false);
  const [code, setCode] = useState('');
  const [verifyError, setVerifyError] = useState('');
  const [resendTimer, setResendTimer] = useState(30);
  const timerRef = useRef(null);
  const recaptchaRef = useRef(null);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);

  const { setUser } = useUser();
  const navigate = useNavigate();

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  useEffect(() => {
    localStorage.setItem('theme', 'light');
    document.body.classList.remove('dark-theme');
  }, []);

  useEffect(() => {
    if (show2FA && resendTimer > 0) {
      timerRef.current = setInterval(() => {
        setResendTimer(prev => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timerRef.current);
  }, [show2FA, resendTimer]);

  const handleChange = e => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));

    if (name === "email") {
      if (value === "") setEmailError("");
      else if (!emailRegex.test(value)) setEmailError("Please enter a valid email address.");
      else setEmailError("");
    }
  };

  const handleCaptchaChange = token => setCaptchaToken(token);

  // единая функция редиректа после успешной аутентификации
  const redirectAfterLogin = (token) => {
    const params = new URLSearchParams(window.location.search);
    const nextFromUrl = params.get('next');
    const nextFromSession = sessionStorage.getItem('next_redirect');
    const next = nextFromUrl || nextFromSession;
  
    if (!next) {
      // дефолт — на главную
      return navigate('/');
    }
  
    sessionStorage.removeItem('next_redirect');
  
    // если абсолютный URL — аккуратно добавим #rt=...
    try {
      const u = new URL(next, window.location.origin); // поддержит и относительные
      const isPreview = (u.origin === 'http://localhost:5001' && u.pathname === '/weekly/preview');
  
      // Если уходим на другой origin или это превью — прокинем токен через hash
      if (token && (u.origin !== window.location.origin || isPreview)) {
        const hash = new URLSearchParams(u.hash.replace(/^#/, ''));
        hash.set('rt', token);
        u.hash = '#' + hash.toString();
      }
  
      window.location.href = u.toString();
    } catch {
      // если вдруг совсем косой next — отправим как есть
      window.location.href = next;
    }
  };


  const handleSubmit = async e => {
    e.preventDefault();
    setError("");
    setVerifyError("");

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

      if (data.success && data.token) {
        try { setUser(data.user, data.token); } catch {}
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        redirectAfterLogin(data.token); // 👈 передаём токен
      } else if (data.success && !data.token) {
        setShow2FA(true);
        setResendTimer(30);
      } else {
        setError(data.message || "Login failed");
        recaptchaRef.current?.reset();
        setCaptchaToken('');
      }
    } catch (err) {
      setError("Network error. Try again.");
      recaptchaRef.current?.reset();
      setCaptchaToken('');
    }
  };

  const handle2FAVerify = async () => {
    setVerifyError('');
    try {
      const res = await fetch("http://localhost:5001/api/verify-2fa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.email, code })
      });
      const data = await res.json();
      if (data.success) {
        try { setUser(data.user, data.token); } catch {}
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        redirectAfterLogin(data.token); // 👈 сюда тоже
      } else {
        setVerifyError(data.message || "Verification failed");
      }
    } catch (err) {
      setVerifyError("Network error. Try again.");
    }
  };

  const handleResendCode = async () => {
    setVerifyError('');
    try {
      const res = await fetch("http://localhost:5001/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, captchaToken }),
        credentials: "include"
      });
      const data = await res.json();
      if (data.success && !data.token) {
        setVerifyError("New code sent to your email.");
        setResendTimer(30);
      } else {
        setVerifyError("Failed to resend code.");
      }
    } catch {
      setVerifyError("Server error while resending code.");
    }
  };

  const onGithubClick = () => {
    // сохраняем next, чтобы после OAuth вернуться туда же
    const params = new URLSearchParams(window.location.search);
    const next = params.get('next');
    if (next) sessionStorage.setItem('next_redirect', next);

    // если бэкенд поддерживает прокидку next — добавим
    const url = new URL("http://localhost:5001/api/github");
    if (next) url.searchParams.set('next', next);
    window.location.href = url.toString();
  };

  return (
    <form onSubmit={handleSubmit} className="p-4" style={{ width: '100%', maxWidth: '400px' }}>
      <div className="text-center mb-3">
        <img src="/logo.png" alt="Trip DVisor" style={{ height: '50px' }} />
      </div>

      <div className="mb-3 d-grid">
        <button
          type="button"
          className="btn btn-outline-dark"
          onClick={onGithubClick}
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
        {emailError && <div className="invalid-feedback">{emailError}</div>}
      </div>

      <div className="mb-3 position-relative">
        <label>Password</label>
        <input
          name="password"
          type={showPassword ? "text" : "password"}
          className="form-control pe-5"
          onChange={handleChange}
          onFocus={() => setPasswordFocused(true)}
          onBlur={() => setPasswordFocused(false)}
          required
          style={{ marginBottom: '0.2rem' }}
        />
        <span
          className="position-absolute"
          style={{
            top: '46%',
            right: '12px',
            transform: 'translateY(-50%)',
            cursor: 'pointer',
            color: '#888',
            fontSize: '1.1rem',
            lineHeight: '1'
          }}
          onClick={() => setShowPassword(prev => !prev)}
        >
          {showPassword ? <FaEyeSlash /> : <FaEye />}
        </span>
        <div className="text-end">
          <Link to="/forgot-password" className="text-decoration-none text-muted" style={{ fontSize: '0.875rem' }}>
            Forgot password?
          </Link>
        </div>
      </div>

      <div className="mb-3">
        <div
          className="captcha-wrapper"
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            marginTop: '1rem',
            marginBottom: '1rem',
            transform: window.innerWidth < 768 ? 'scale(0.82)' : 'scale(1)',
            transformOrigin: 'center',
            transition: 'transform 0.3s ease'
          }}
        >
          <ReCAPTCHA
            ref={recaptchaRef}
            sitekey="6LdTZGwrAAAAAOs5n3cyHEAebDLsfRcyMd4-Fj67"
            onChange={handleCaptchaChange}
          />
        </div>
      </div>

      {error && (
        <div className="alert alert-danger text-center" role="alert">
          {error}
        </div>
      )}

      {!show2FA && (
        <>
          <button type="submit" className="btn btn-primary w-100">
            Sign In
          </button>
          <p className="text-center mt-3">
            Don’t have an account? <Link to="/register">Sign up</Link>
          </p>
        </>
      )}

      {show2FA && (
        <div className="mt-4">
          <label>Enter the verification code from your email</label>
          <input
            type="text"
            className="form-control mt-2"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            autoFocus
          />
          {verifyError && <div className="text-danger mt-1">{verifyError}</div>}
          <button type="button" className="btn btn-success w-100 mt-3" onClick={handle2FAVerify}>
            Verify Code
          </button>

          <div className="text-center mt-2">
            {resendTimer > 0 ? (
              <span className="text-muted">You can resend the code in {resendTimer}s</span>
            ) : (
              <button type="button" className="btn btn-link" onClick={handleResendCode}>
                Resend Code
              </button>
            )}
          </div>
        </div>
      )}
    </form>
  );
}

export default Login;
