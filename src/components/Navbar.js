import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';

function Navbar() {
  const { user, clearUser } = useUser();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearUser();
    navigate('/login');
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm px-4">
      <Link className="navbar-brand" to="/">Trip DVisor</Link>
      <div className="ms-auto d-flex align-items-center">
        {user ? (
          <button className="btn btn-outline-danger btn-sm" onClick={handleLogout}>
            Sign Out
          </button>
        ) : (
          <Link className="btn btn-outline-primary" to="/login">Sign In</Link>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
