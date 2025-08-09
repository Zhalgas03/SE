import React, { createContext, useContext, useState, useEffect } from "react";

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const storedUser = (() => {
    try {
      return JSON.parse(localStorage.getItem("user"));
    } catch {
      return null;
    }
  })();
  const storedToken = localStorage.getItem("token");

  const [user, setUser] = useState(storedUser || null);
  const [token, setToken] = useState(storedToken || null);

  const saveUser = (userData, tokenData) => {
    if (userData && tokenData) {
      setUser(userData);
      setToken(tokenData);
      localStorage.setItem("user", JSON.stringify(userData));
      localStorage.setItem("token", tokenData);
    }
  };

  const clearUser = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("user");
    localStorage.removeItem("token");
  };

  const checkTokenValidity = async () => {
    const freshToken = localStorage.getItem("token");
    if (!freshToken) {
      clearUser();
      return;
    }

    try {
      const res = await fetch("http://localhost:5001/api/user/profile", {
        headers: {
          Authorization: `Bearer ${freshToken}`,
        },
        credentials: "include",
      });

      const data = await res.json();

      if (res.status === 401 || !data.success) {
        clearUser();
      } else if (data.user) {
        setUser(data.user);
        setToken(freshToken);
        localStorage.setItem("user", JSON.stringify(data.user));
      }
    } catch (err) {
      clearUser();
    }
  };

  useEffect(() => {
    checkTokenValidity();
  }, []);

  const isAuthenticated = !!user;
  const isAdmin = user?.role === "admin";
  const isPremium = user?.role === "premium"; // 👈 добавили

  return (
    <UserContext.Provider
      value={{
        user,
        token,
        setUser: saveUser,
        clearUser,
        isAuthenticated,
        isAdmin,
        isPremium, // 👈 добавили
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
