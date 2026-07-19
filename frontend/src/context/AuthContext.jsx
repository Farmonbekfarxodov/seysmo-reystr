import React, { createContext, useContext, useEffect, useState } from "react";

import { authApi } from "../api/endpoints";
import { getTokens, setTokens } from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    const tokens = getTokens();
    if (tokens?.user) {
      setUser(tokens.user);
    }
    setInitializing(false);
  }, []);

  async function login(loginValue, password) {
    const response = await authApi.login(loginValue, password);
    const { access, refresh, user: userData } = response.data;
    setTokens({ access, refresh, user: userData });
    setUser(userData);
    return userData;
  }

  function updateUser(patch) {
    setUser((prev) => {
      const next = { ...prev, ...patch };
      const tokens = getTokens();
      if (tokens) setTokens({ ...tokens, user: next });
      return next;
    });
  }

  function logout() {
    setTokens(null);
    setUser(null);
  }

  const value = { user, initializing, login, logout, updateUser, isAuthenticated: !!user };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
