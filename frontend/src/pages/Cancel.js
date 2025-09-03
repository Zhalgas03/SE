import React from 'react';
import { Link } from 'react-router-dom';

function Cancel() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
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
          color: 'var(--error-color)',
        }}
      >
        Payment Cancelled
      </h1>
      <p
        style={{
          fontSize: '1.1rem',
          marginBottom: '2rem',
          color: 'var(--text-color)',
        }}
      >
        Looks like you cancelled the subscription process.
      </p>
      <Link to="/account">
        <button
          style={{
            padding: '0.6rem 1.5rem',
            borderRadius: '9999px',
            fontWeight: '600',
            fontSize: '1rem',
            backgroundColor: 'var(--btn-bg)',
            color: 'var(--btn-text)',
            border: 'none',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          }}
        >
          Back to Account
        </button>
      </Link>
    </div>
  );
}

export default Cancel;