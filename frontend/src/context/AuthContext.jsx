import { createContext, useContext, useEffect, useState } from "react";
import { clearTokens, getAccessToken, onSessionExpired } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(getAccessToken()));

  useEffect(() => onSessionExpired(() => setIsAuthenticated(false)), []);

  function markAuthenticated() {
    setIsAuthenticated(true);
  }

  function markLoggedOut() {
    clearTokens();
    setIsAuthenticated(false);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, markAuthenticated, markLoggedOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
