import { useEffect, useState } from "react";
import { clearTokens, getAccessToken, onSessionExpired } from "../api/client";
import AuthContext from "./auth-context";

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
