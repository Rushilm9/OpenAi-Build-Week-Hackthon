import { createContext, useContext, useState, useCallback } from "react";
import type { ReactNode } from "react";
import type { AuthUser } from "../types";
import { apiService } from "../services/api";

const STORAGE_KEY = "quantai_user";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? (JSON.parse(stored) as AuthUser) : null;
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
  });
  const isLoading = false;

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiService.authLogin(email, password);
    setUser(response.user);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(response.user));
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const response = await apiService.authRegister(email, password);
    setUser(response.user);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(response.user));
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiService.authLogout();
    } catch {
      // Server might be down — still clear local state
    }
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// This hook shares the provider's context by design; keeping it here avoids a
// circular module dependency while the provider remains the only component.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
