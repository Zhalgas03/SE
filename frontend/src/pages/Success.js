import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import axios from 'axios';
import Confetti from 'react-confetti';
import { useWindowSize } from '@react-hook/window-size';

function Success() {
  const { setUser } = useUser();
  const [width, height] = useWindowSize();
  const [showConfetti, setShowConfetti] = useState(true);

  useEffect(() => {
    // Автоматическое исчезновение конфетти через 3 секунды
    const timer = setTimeout(() => {
      setShowConfetti(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      try {
        const res = await axios.get('http://localhost:5001/api/user/profile', {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        });

        if (res.data.success && res.data.user) {
          setUser(
            {
              username: res.data.user.username,
              is_subscribed: res.data.user.is_subscribed,
            },
            token
          );
        }
      } catch (err) {
        console.error('❌ Failed to fetch user after payment success', err);
      }
    };

    fetchUser();
  }, [setUser]);

  return (
    <>
      {showConfetti && (
        <Confetti
          width={width}
          height={height}
          numberOfPieces={180}
          gravity={0.3}
          recycle={false}
        />
      )}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '90vh',
          backgroundColor: 'var(--bg)',
          color: 'var(--text-color)',
          textAlign: 'center',
          padding: '2rem',
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
          Payment Successful
        </h1>
        <p
          style={{
            fontSize: '1.1rem',
            marginBottom: '2rem',
            color: 'var(--text-color)',
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
    </>
  );
}

export default Success;