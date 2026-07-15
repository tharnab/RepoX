"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

interface User {
  id: number;
  login: string;
  avatar_url: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: () => void;
  loginWithDifferentAccount: () => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: () => {},
  loginWithDifferentAccount: () => {},
  logout: async () => {},
});

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/auth/me`, {
        credentials: "include",
      });
      const data = await res.json();
      if (data.authenticated) {
        setUser(data.user);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = () => {
    window.location.href = `${API_URL}/auth/github/login`;
  };

  const loginWithDifferentAccount = () => {
    // Open GitHub logout in a hidden iframe, then redirect
    const iframe = document.createElement("iframe");
    iframe.src = "https://github.com/logout";
    iframe.style.display = "none";
    document.body.appendChild(iframe);
    
    setTimeout(() => {
      document.body.removeChild(iframe);
      window.location.href = `${API_URL}/auth/github/login`;
    }, 1000);
  };

  const handleLogout = async () => {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        loginWithDifferentAccount,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}