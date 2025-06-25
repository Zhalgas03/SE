import React, { createContext, useContext, useState, useEffect } from 'react';

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const storedUser = JSON.parse(localStorage.getItem('user'));
  const storedToken = localStorage.getItem('token');
  const [user, setUser] = useState(storedUser || null);
  const [token, setToken] = useState(storedToken || null);

  const saveUser = (userData, tokenData) => {
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('token', tokenData);
    setUser(userData);
    setToken(tokenData);
  };

  const clearUser = () => {
    localStorage.clear();
    setUser(null);
    setToken(null);
  };

  const checkTokenValidity = async () => {
    if (!storedToken) return;
    try {
      const res = await fetch('http://localhost:5001/api/account/settings', {
        headers: { Authorization: `Bearer ${storedToken}` },
        credentials: 'include',
      });

      if (res.status === 401) {
        clearUser();
      }
    } catch (err) {
      clearUser();
    }
  };

  useEffect(() => {
    checkTokenValidity();
  }, []);

  return (
    <UserContext.Provider value={{ user, token, setUser: saveUser, clearUser }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
