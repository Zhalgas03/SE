import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import axios from 'axios';

function Success() {
  const { setUser } = useUser();

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      try {
        const res = await axios.get('http://localhost:5001/api/user/profile', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          withCredentials: true,
        });

        if (res.data.success && res.data.user) {
          setUser({ username: res.data.user.username, is_subscribed: res.data.user.is_subscribed }, token);
        }
      } catch (err) {
        console.error('❌ Failed to fetch user after payment success', err);
      }
    };

    fetchUser();
  }, [setUser]);

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        paddingTop: '12vh',
        paddingBottom: '4vh',
        minHeight: 'auto',
        backgroundColor: 'var(--bg)',
        color: 'var(--text-color)',
      }}
    >
      <div
        style={{
          maxWidth: '500px',
          width: '100%',
          textAlign: 'center',
          padding: '1rem',
        }}
      >
        <h1
          style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            marginBottom: '1rem',
            color: 'var(--success-color, #22c55e)',
          }}
        >
          ✅ Payment Successful
        </h1>
        <p
          style={{
            fontSize: '1.1rem',
            marginBottom: '1.5rem',
            color: 'var(--muted-text)',
          }}
        >
          Thank you for subscribing to TripDVisor Premium!
        </p>
        <Link to="/account">
          <button
            style={{
              padding: '0.6rem 1.5rem',
              borderRadius: '9999px',
              fontWeight: '600',
              fontSize: '1rem',
              backgroundColor: 'var(--btn-bg, #2563eb)',
              color: 'var(--btn-text, #fff)',
              border: 'none',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}
          >
            Go to Account
          </button>
        </Link>
      </div>
    </div>
  );
}

export default Success;
