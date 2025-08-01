import React, { createContext, useContext, useState, useEffect } from 'react';

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const storedUser = JSON.parse(localStorage.getItem('user'));
  const storedToken = localStorage.getItem('token');

  const [user, setUser] = useState(storedUser || null);
  const [token, setToken] = useState(storedToken || null);

  const saveUser = (userData, tokenData) => {
    if (userData && tokenData) {
      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('token', tokenData);
      setUser(userData);
      setToken(tokenData);
    }
  };

  const clearUser = () => {
    localStorage.clear();
    setUser(null);
    setToken(null);
  };

  const checkTokenValidity = async () => {
    const freshToken = localStorage.getItem('token');
    if (!freshToken) return;

    try {
      const res = await fetch('http://localhost:5001/api/user/profile', {
        headers: { Authorization: `Bearer ${freshToken}` },
        credentials: 'include',
      });

      const data = await res.json();

      if (res.status === 401 || !data.success) {
        clearUser();
      } else if (data.user) {
        const userObj = {
          username: data.user.username,
          is_subscribed: data.user.is_subscribed || false
        };
        localStorage.setItem('user', JSON.stringify(userObj));
        setUser(userObj);
        setToken(freshToken);
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
